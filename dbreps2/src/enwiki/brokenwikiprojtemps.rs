/*
Copyright 2011, 2013 bjweeks, MZMcBride, Tim Landscheidt
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
use dbreps2::{str_vec, DbrLink, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    tl_title: String,
    count: u64,
}

pub struct BrokenWikiProjTemps {}

#[async_trait::async_trait]
impl Report<Row> for BrokenWikiProjTemps {
    fn title(&self) -> &'static str {
        "Broken WikiProject templates"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* brokenwikiprojtemps.rs SLOW_OK */
SELECT
  tl_title,
  COUNT(*)
FROM
  templatelinks
  JOIN linktarget ON tl_target_id = lt_id
  JOIN page AS p1 ON tl_from = p1.page_id
  LEFT JOIN page AS p2 ON lt_namespace = p2.page_namespace
  AND lt_title = p2.page_title
WHERE
  lt_namespace = 10
  AND lt_title LIKE 'Wiki%'
  AND lt_title RLIKE 'Wiki[_]?[Pp]roject.*'
  AND lt_title NOT LIKE '%/importance'
  AND lt_title NOT LIKE '%/class'
  AND p2.page_id IS NULL
GROUP BY
  lt_title;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(tl_title, count)| Row {
                tl_title,
                count,
            })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Template", "Transclusions"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![DbrLink::new(&row.tl_title), row.count]
    }

    fn code(&self) -> &'static str {
        include_str!("brokenwikiprojtemps.rs")
    }
}
