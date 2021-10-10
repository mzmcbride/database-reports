/*
Copyright 2008 bjweeks, MZMcBride
Copyright 2021 Kunal Mehta <legoktm@debian.org>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
use anyhow::Result;
use chrono::Duration;
use log::info;
use mysql_async::{Conn, Pool};
use regex::Regex;
use std::fmt;
use tokio::fs;

mod api;
mod config;

#[macro_export]
macro_rules! str_vec {
    ( $( $item:expr ),* ) => {
        {
            let mut temp_vec = Vec::new();
            $(
                temp_vec.push($item.to_string());
            )*
            temp_vec
        }
    };
}

const INDEX_WIKITEXT: &str = r#"{{DBR index}}

{{DBR footer}}
"#;

pub async fn load_config() -> Result<config::Config> {
    let path = dirs::home_dir().unwrap().join(".dbreps.toml");
    let contents = fs::read_to_string(path).await?;
    Ok(toml::from_str(&contents)?)
}

pub enum Frequency {
    Daily,
    Weekly,
    Fortnightly,
    Monthly,
}

impl Frequency {
    fn to_duration(&self) -> Duration {
        match &self {
            Frequency::Daily => Duration::days(1),
            Frequency::Weekly => Duration::weeks(1),
            Frequency::Fortnightly => Duration::weeks(2),
            Frequency::Monthly => Duration::weeks(4),
        }
    }
}

#[async_trait::async_trait]
pub trait Report<T: Send + Sync> {
    // TODO: Make this per-wiki/language
    fn title(&self) -> &'static str;

    fn get_title(&self) -> String {
        format!("Project:Database reports/{}", self.title())
    }

    fn frequency(&self) -> Frequency;

    fn rows_per_page(&self) -> Option<usize> {
        None
    }

    fn enumerate(&self) -> bool {
        true
    }

    fn query(&self) -> &'static str;

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<T>>;

    fn intro(&self) -> &'static str {
        self.title()
    }

    fn headings(&self) -> Vec<&'static str>;

    fn format_row(&self, row: &T) -> Vec<String>;

    fn code(&self) -> &'static str;

    fn get_intro(&self) -> String {
        // TODO: is replag something we still need to care about? meh
        let mut intro = vec![
            format!(
                "{}; data as of <onlyinclude>~~~~~</onlyinclude>.",
                self.intro()
            ),
            r#"{| class="wikitable sortable"
|- style="white-space:nowrap;"
"#
            .to_string(),
        ];
        if self.enumerate() {
            intro.push("! No.".to_string());
        }
        for heading in self.headings() {
            intro.push(format!("! {}", heading));
        }
        intro.join("\n")
    }

    fn get_footer(&self) -> String {
        "|-\n|}\n{{DBR footer}}\n".to_string()
    }

    fn needs_update(&self, old_text: &str) -> Result<bool> {
        use chrono::prelude::*;
        let re = Regex::new("<onlyinclude>(.*?)</onlyinclude>").unwrap();
        let ts = match re.captures(old_text) {
            Some(cap) => cap[1].to_string(),
            None => {
                // No match, it needs an update!
                return Ok(true);
            }
        };
        let dt = Utc.datetime_from_str(&ts, "%H:%M, %d %B %Y (UTC)")?;
        let now = Utc::now();
        if (dt + self.frequency().to_duration()) < now {
            Ok(true)
        } else {
            Ok(false)
        }
    }

    fn build_page(&self, rows: &[T], index: usize) -> String {
        // The first row starts at the # of previous pages times rows per page
        let mut row_num = (index - 1) * self.rows_per_page().unwrap_or(0);
        let mut text = vec![self.get_intro()];
        for row in rows {
            row_num += 1;
            text.push("|-".to_string());
            if self.enumerate() {
                text.push(format!("| {}", row_num));
            }
            for item in self.format_row(row) {
                text.push(format!("| {}", item));
            }
        }
        text.push(self.get_footer());
        text.join("\n")
    }

    async fn run(&self, client: &mwapi::Client, pool: &Pool) -> Result<()> {
        info!(
            "{}: Checking when last results were published...",
            self.get_title()
        );
        let title_for_update_check = match self.rows_per_page() {
            Some(_) => format!("{}/1", self.get_title()),
            None => self.get_title(),
        };
        if api::exists(client, &title_for_update_check).await? {
            let old_text =
                api::get_wikitext(client, &title_for_update_check).await?;
            if !self.needs_update(&old_text)? {
                info!(
                    "{}: Report is still up to date, skipping update.",
                    self.get_title()
                );
                return Ok(());
            }
        }
        let mut conn = pool.get_conn().await?;
        info!("{}: Starting query...", self.get_title());
        let rows = self.run_query(&mut conn).await?;
        info!(
            "{}: Query finished, found {} rows",
            self.get_title(),
            &rows.len()
        );
        match self.rows_per_page() {
            Some(rows_per_page) => {
                let iter = rows.chunks(rows_per_page);
                let mut index = 0;
                for chunk in iter {
                    index += 1;
                    let text = self.build_page(chunk, index);
                    api::save_page(
                        client,
                        &format!("{}/{}", self.get_title(), index),
                        &text,
                    )
                    .await?;
                }
                // Now "Blank" any other subpages
                loop {
                    index += 1;
                    let title = format!("{}/{}", self.get_title(), index);
                    if !api::exists(client, &title).await? {
                        break;
                    }
                    api::save_page(client, &title, "{{intentionally blank}}")
                        .await?;
                }
                // Finally make sure the index page is up to date
                api::save_page(client, &self.get_title(), INDEX_WIKITEXT)
                    .await?;
            }
            None => {
                // Just dump it all into one page
                let text = self.build_page(&rows, 1);
                api::save_page(client, &self.get_title(), &text).await?;
            }
        }
        // Finally, publish the /Configuration subpage
        let days = match self.frequency().to_duration().num_days() {
            // every day
            1 => "day".to_string(),
            // every X days
            num => format!("{} days", num),
        };
        let config = format!(
            r#"This report is updated every {}.
== Source code ==
<syntaxhighlight lang="rust">
{}
</syntaxhighlight>
"#,
            days,
            self.code()
        );
        api::save_page(
            client,
            &format!("{}/Configuration", self.get_title()),
            &config,
        )
        .await?;

        Ok(())
    }
}

pub struct DbrLink(String);

impl DbrLink {
    pub fn new(target: &str) -> Self {
        Self(target.to_string())
    }
}

impl fmt::Display for DbrLink {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{{{{dbr link|1={}}}}}", self.0)
    }
}

pub struct Linker(u32, String);

impl Linker {
    pub fn new(ns: u32, target: &str) -> Self {
        Self(ns, target.to_string())
    }
}

impl fmt::Display for Linker {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        // TODO: be smarter about ns 0, and leading colons for files/cats
        write!(f, "[[:{{{{ns:{}}}}}:{}]]", self.0, self.1)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dbrlink() {
        assert_eq!(
            DbrLink::new("Taylor Swift").to_string(),
            "{{dbr link|1=Taylor Swift}}".to_string()
        );
    }

    #[test]
    fn test_linker() {
        assert_eq!(
            Linker::new(0, "Foo bar").to_string(),
            "[[:{{ns:0}}:Foo bar]]".to_string()
        )
    }
}
