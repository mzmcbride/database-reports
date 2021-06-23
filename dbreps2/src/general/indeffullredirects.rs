/*
Copyright 2008, 2013 bjweeks, CBM, MZMcBride, Tim Landscheidt
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
use dbreps2::{Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
    actor_name: String,
    log_timestamp: String,
    comment_text: String,
}

pub struct IndefFullRedirects {}

#[async_trait::async_trait]
impl Report<Row> for IndefFullRedirects {
    fn title(&self) -> &'static str {
        "Indefinitely fully protected redirects"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(800)
    }

    fn query(&self) -> &'static str {
        r#"
/* indeffullredirects.rs SLOW_OK */
SELECT
  page_title,
  actor_name,
  log_timestamp,
  comment_text
FROM
  page_restrictions
  JOIN page ON page_id = pr_page
  JOIN logging_userindex ON page_namespace = log_namespace
  AND page_title = log_title
  AND log_type = 'protect'
  JOIN actor_user ON log_actor = actor_id
  JOIN comment ON log_comment_id = comment_id
WHERE
  page_namespace = 0
  AND pr_type = 'edit'
  AND pr_level = 'sysop'
  AND pr_expiry = 'infinity'
  AND page_is_redirect = 1
ORDER BY
  1,
  3 DESC;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(page_title, actor_name, log_timestamp, comment_text)| Row {
                    page_title,
                    actor_name,
                    log_timestamp,
                    comment_text,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Redirects that are indefinitely fully protected from editing; {asof}."
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Redirect", "Protector", "Timestamp", "Reason"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        // TODO: Improve this interface
        let mut fmt = vec![];
        fmt.push(format!("{{{{plthnr|1={}}}}}", &row.page_title));
        fmt.push(format!("[[User talk:{}|]]", &row.actor_name));
        fmt.push(row.log_timestamp.to_string());
        fmt.push(format!("<nowiki>{}</nowiki>", &row.comment_text));

        fmt
    }

    fn code(&self) -> &'static str {
        include_str!("indeffullredirects.rs")
    }
}
