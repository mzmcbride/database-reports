/*
Copyright 2008, 2013 bjweeks, MZMcBride, Tim Landscheidt
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
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
}

pub struct UserCats {}

impl Report<Row> for UserCats {
    fn title(&self) -> &'static str {
        "User categories"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(2250)
    }

    fn query(&self) -> &'static str {
        r"
/* usercats.rs SLOW_OK */
SELECT
  page_title
FROM
  page
WHERE
  page_namespace = 14
  AND CONVERT(page_title USING utf8mb4) RLIKE '(?i)(wikipedian|\buser|wikiproject.*(participant|members)|(participant|members).*wikiproject)';
"
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title,)| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Categories that contain \"(wikipedian|\\buser)\", \"wikiproject\" and \"participants\", or \"wikiproject\" and \"members\""
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!(
            "[[:Category:{}|{}]]",
            &row.page_title, &row.page_title
        )]
    }

    fn code(&self) -> &'static str {
        include_str!("usercats.rs")
    }
}
