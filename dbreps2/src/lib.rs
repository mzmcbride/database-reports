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
use tokio::fs;

mod api;
mod config;

pub async fn load_config() -> Result<config::Config> {
    let path = dirs_next::home_dir().unwrap().join(".dbreps.toml");
    let contents = fs::read_to_string(path).await?;
    Ok(toml::from_str(&contents)?)
}

pub enum Frequency {
    Weekly,
    Fortnightly,
    Monthly,
}

impl Frequency {
    fn to_duration(&self) -> Duration {
        match &self {
            Frequency::Weekly => Duration::weeks(1),
            Frequency::Fortnightly => Duration::weeks(2),
            Frequency::Monthly => Duration::weeks(4),
        }
    }
}

#[async_trait::async_trait]
pub trait Report<T: Send> {
    // TODO: Make this per-wiki/language
    fn title(&self) -> &'static str;

    fn frequency(&self) -> Frequency;

    fn query(&self) -> &'static str;

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<T>>;

    fn intro(&self) -> &'static str;

    fn headings(&self) -> Vec<&'static str>;

    fn format_row(&self, row: &T) -> Vec<String>;

    fn get_intro(&self) -> String {
        // TODO: is replag something we still need to care about? meh
        self.intro()
            .replace("{asof}", "data as of <onlyinclude>~~~~~</onlyinclude>")
    }

    async fn publish(&self, client: &mwapi::Client, text: &str) -> Result<()> {
        info!("Updating [[{}]]", self.title());
        info!("{}", &text);
        api::save_page(client, self.title(), text).await?;
        Ok(())
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

    async fn run(&self, client: &mwapi::Client) -> Result<()> {
        info!(
            "{}: Checking when last results were published...",
            self.title()
        );
        let old_text = api::get_wikitext(client, self.title()).await?;
        if !self.needs_update(&old_text)? {
            info!(
                "{}: Report is still up to date, skipping update.",
                self.title()
            );
            return Ok(());
        }
        info!("Connecting to MySQL...");
        let db_url = toolforge::connection_info!("enwiki", ANALYTICS)?;
        let pool = Pool::new(db_url.to_string());
        let mut conn = pool.get_conn().await?;
        info!("{}: Starting query...", self.title());
        let rows = self.run_query(&mut conn).await?;
        info!("{}: Query finished", self.title());
        let mut text = vec![
            self.get_intro(),
            r#"{| class="wikitable sortable"
|- style="white-space:nowrap;"
"#
            .to_string(),
        ];
        for heading in self.headings() {
            text.push(format!("! {}", heading));
        }
        for row in rows {
            text.push("|-".to_string());
            for item in self.format_row(&row) {
                text.push(format!("| {}", item));
            }
        }
        text.push("|-".to_string());
        text.push("|}".to_string());
        text.push("".to_string());
        text.push("[[Category:Active Wikipedia database reports]]".to_string());

        self.publish(client, &text.join("\n")).await?;

        Ok(())
    }
}
