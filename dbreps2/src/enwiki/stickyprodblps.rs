/*
Copyright 2012-2013 MZMcBride, Tim Landscheidt
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
    rev_timestamp: String,
    is_categorized: u32,
}

pub struct StickyProdBLPs {}

#[async_trait::async_trait]
impl Report<Row> for StickyProdBLPs {
    fn title(&self) -> &'static str {
        "Biographies of living people possibly eligible for deletion"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* stickyprodblps.rs SLOW_OK */
SELECT
  page_title,
  rev_timestamp,
  EXISTS(
    SELECT
      1
    FROM
      categorylinks
    WHERE
      cl_from = page_id
      AND cl_to IN (
        'BLP_articles_proposed_for_deletion',
        'Articles_for_deletion'
      )
  )
FROM
  page
  JOIN revision ON rev_page = page_id
  JOIN categorylinks ON cl_from = page_id
WHERE
  cl_to = 'All_unreferenced_BLPs'
  AND page_namespace = 0
  AND page_is_redirect = 0
  AND rev_timestamp = (
    SELECT
      MIN(rev_timestamp)
    FROM
      revision AS last
    WHERE
      last.rev_page = page_id
  )
  AND rev_timestamp > '20100318000000';
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(page_title, rev_timestamp, is_categorized)| Row {
                    page_title,
                    rev_timestamp,
                    is_categorized,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Biographies of living people possibly eligible for deletion. \
        Biographies in [[:Category:BLP articles proposed for deletion]] \
        or [[:Category:Articles for deletion]] are marked in bold"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography", "First edit"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        let mut link = format!("{{{{dbr link|1={}}}}}", row.page_title);
        if row.is_categorized == 1 {
            link = format!("<b>{}</b>", &link);
        }
        str_vec![link, row.rev_timestamp]
    }

    fn code(&self) -> &'static str {
        include_str!("linkedmisspellings.rs")
    }
}
