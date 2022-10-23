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
use log::{error, info};
use mwbot::{Bot, Page, SaveOptions};
use mysql_async::{Conn, Pool};
use regex::Regex;
use std::fmt;
use time::format_description::FormatItem;
use time::macros::format_description;
use time::{Duration, OffsetDateTime, PrimitiveDateTime};
use tokio::fs;

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

const SIG_TIMESTAMP: &[FormatItem] = format_description!(
    "[hour]:[minute], [day padding:none] [month repr:long] [year] (UTC)"
);

const DB_TIMESTAMP: &[FormatItem] =
    format_description!("[year][month][day][hour][minute][second]");

const Y_M_D_TIMESTAMP: &[FormatItem] =
    format_description!("[year]-[month]-[day]");

const INDEX_WIKITEXT: &str = r#"{{DBR index}}
{{DBR footer}}
"#;

const BLANK_WIKITEXT: &str = r#"{{intentionally blank}}"#;

pub async fn load_config() -> Result<config::Config> {
    let path = dirs::home_dir().unwrap().join(".dbreps.toml");
    let contents = fs::read_to_string(path).await?;
    Ok(toml::from_str(&contents)?)
}

async fn save_page(page: Page, text: String) -> Result<()> {
    info!("Updating [[{}]]", page.title());
    info!("{}", &text);
    page.save(text, &SaveOptions::summary("Bot: updating database report"))
        .await?;
    Ok(())
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

    fn static_row_numbers(&self) -> bool {
        false
    }

    fn enumerate(&self) -> bool {
        !self.static_row_numbers()
    }

    fn query(&self) -> &'static str;

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<T>>;

    fn intro(&self) -> &'static str {
        self.title()
    }

    fn headings(&self) -> Vec<&'static str>;

    fn format_row(&self, row: &T) -> Vec<String>;

    fn code(&self) -> &'static str;

    fn get_intro(&self, _index: usize) -> String {
        // TODO: is replag something we still need to care about? meh
        let mut intro = vec![format!(
            "{}; data as of <onlyinclude>~~~~~</onlyinclude>.\n",
            self.intro()
        )];
        if self.static_row_numbers() {
            intro.push("{{static row numbers}}".to_string());
        }
        let mut classes = vec!["wikitable", "sortable"];
        if self.static_row_numbers() {
            classes.extend(["static-row-numbers", "static-row-header-text"]);
        }
        intro.push(format!(
            r#"{{| class="{}"
|- style="white-space: nowrap;""#,
            classes.join(" ")
        ));
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
        let re = Regex::new("<onlyinclude>(.*?)</onlyinclude>").unwrap();
        let ts = match re.captures(old_text) {
            Some(cap) => cap[1].to_string(),
            None => {
                // No match, it needs an update!
                return Ok(true);
            }
        };
        let dt = PrimitiveDateTime::parse(&ts, &SIG_TIMESTAMP)?.assume_utc();
        let now = OffsetDateTime::now_utc();
        let skew = Duration::minutes(20);
        if (dt + self.frequency().to_duration() - skew) < now {
            Ok(true)
        } else {
            Ok(false)
        }
    }

    fn build_page(&self, rows: &[T], index: usize) -> String {
        // The first row starts at the # of previous pages times rows per page
        let mut row_num = (index - 1) * self.rows_per_page().unwrap_or(0);
        let mut text = vec![self.get_intro(index)];
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

    async fn really_run(&self, runner: &Runner) {
        let should_run = match &runner.report {
            Some(wanted) => wanted == self.title(),
            None => true,
        };
        let debug_mode = runner.report.is_some();
        if should_run {
            match self.run(debug_mode, &runner.bot, &runner.pool).await {
                Ok(_) => {}
                Err(err) => {
                    error!("{}", err.to_string());
                }
            }
        }
    }

    async fn post_run(&self, _bot: &Bot, _debug_mode: bool) -> Result<()> {
        Ok(())
    }

    fn subpage(&self, index: usize) -> String {
        format!("{}/{}", self.get_title(), index)
    }

    fn update_index(&self) -> bool {
        true
    }

    async fn run(
        &self,
        debug_mode: bool,
        bot: &Bot,
        pool: &Pool,
    ) -> Result<()> {
        // Bypass needs update check when --report is passed
        if debug_mode {
            info!("Passed --report, we're in debug mode");
        } else {
            info!(
                "{}: Checking when last results were published...",
                self.get_title()
            );
            let title_for_update_check = match self.rows_per_page() {
                Some(_) => self.subpage(1),
                None => self.get_title(),
            };
            let page = bot.page(&title_for_update_check)?;
            if page.exists().await? {
                let old_text = page.wikitext().await?;
                if !self.needs_update(&old_text)? {
                    info!(
                        "{}: Report is still up to date, skipping update.",
                        self.get_title()
                    );
                    return Ok(());
                }
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
                    if debug_mode {
                        info!("{}", &text);
                    } else {
                        let page = bot.page(&self.subpage(index))?;
                        save_page(page, text).await?;
                    }
                }
                // Now "Blank" any other subpages
                loop {
                    index += 1;
                    let page = bot.page(&self.subpage(index))?;
                    if !page.exists().await? {
                        break;
                    }
                    if debug_mode {
                        info!("{}", BLANK_WIKITEXT);
                    } else {
                        save_page(page, BLANK_WIKITEXT.to_string()).await?;
                    }
                }
                // Finally make sure the index page is up to date
                if self.update_index() {
                    if debug_mode {
                        info!("{}", INDEX_WIKITEXT);
                    } else {
                        save_page(
                            bot.page(&self.get_title())?,
                            INDEX_WIKITEXT.to_string(),
                        )
                        .await?;
                    }
                }
            }
            None => {
                // Just dump it all into one page
                let text = self.build_page(&rows, 1);
                if debug_mode {
                    info!("{}", &text);
                } else {
                    save_page(bot.page(&self.get_title())?, text).await?;
                }
            }
        }
        // Finally, publish the /Configuration subpage
        let days = match self.frequency().to_duration().whole_days() {
            // every day
            1 => "day".to_string(),
            // every X days
            num => format!("{} days", num),
        };
        let config = format!(
            r#"This report is updated every {}.

== Source code ==
<syntaxhighlight lang="rust">
{}</syntaxhighlight>
"#,
            days,
            self.code()
        );
        if debug_mode {
            info!("{}", &config);
        } else {
            save_page(
                bot.page(&format!("{}/Configuration", self.get_title()))?,
                config,
            )
            .await?;
        }
        self.post_run(bot, debug_mode).await?;
        Ok(())
    }
}

pub struct Runner {
    bot: Bot,
    pub pool: Pool,
    /// Requested report with --report
    report: Option<String>,
}

impl Runner {
    pub async fn new(
        domain: &str,
        dbname: &str,
        report: Option<String>,
    ) -> Result<Self> {
        let cfg = load_config().await?;
        let bot = Bot::builder(
            format!("https://{}/w/api.php", domain),
            format!("https://{}/api/rest_v1", domain),
        )
        .set_oauth2_token(cfg.auth.username, cfg.auth.oauth2_token)
        .build()
        .await?;
        info!("Setting up MySQL connection pool for {}...", dbname);
        let pool = Pool::new(
            toolforge::connection_info!(dbname, ANALYTICS)?.to_string(),
        );
        Ok(Self { bot, pool, report })
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
        write!(f, "{{{{dbr link|1={}}}}}", self.0.replace('_', " "))
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
        let colon = match self.0 {
            // File | Category
            6 | 14 => ":",
            _ => "",
        };
        let ns_prefix = match self.0 {
            0 => "".to_string(),
            num => format!("{{{{subst:ns:{}}}}}:", num),
        };

        write!(f, "[[{}{}{}]]", colon, ns_prefix, self.1)
    }
}

/// "Escape" a block reason so it's safe for display
/// in a table context
pub fn escape_reason(text: &str) -> String {
    text
        // Escape templates
        .replace("{{", "{{tl|")
        // And HTML comments
        .replace("<!--", "<nowiki><!--</nowiki>")
}

pub fn y_m_d(input: &str) -> String {
    let dt = match PrimitiveDateTime::parse(input, &DB_TIMESTAMP) {
        Ok(dt) => dt.assume_utc(),
        Err(_) => return input.to_string(),
    };
    dt.format(Y_M_D_TIMESTAMP)
        .unwrap_or_else(|_| input.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use time::macros::{date, time};

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
            "[[Foo bar]]".to_string()
        );
        assert_eq!(
            Linker::new(1, "Foo bar").to_string(),
            "[[{{subst:ns:1}}:Foo bar]]".to_string()
        );
        assert_eq!(
            Linker::new(6, "Foo bar").to_string(),
            "[[:{{subst:ns:6}}:Foo bar]]".to_string()
        );
    }

    #[test]
    fn test_escape_reason() {
        assert_eq!(
            escape_reason("{{foo}} [[bar]] <!-- baz -->"),
            "{{tl|foo}} [[bar]] <nowiki><!--</nowiki> baz -->".to_string()
        )
    }

    #[test]
    fn test_timestamp() {
        let ts = "14:31, 3 January 2022 (UTC)";
        let dt = PrimitiveDateTime::parse(&ts, &SIG_TIMESTAMP)
            .unwrap()
            .assume_utc();
        assert_eq!(dt.date(), date!(2022 - 01 - 03));
        assert_eq!(dt.time(), time!(14:31:00));
    }

    #[test]
    fn test_y_m_d() {
        assert_eq!(y_m_d("20010115192713"), "2001-01-15".to_string());
        assert_eq!(y_m_d("20221015001541"), "2022-10-15".to_string());
    }
}
