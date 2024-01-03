/*
Copyright 2008, 2013 bjweeks, MZMcBride, Tim Landscheidt
Copyright 2024 Kunal Mehta <legoktm@debian.org>

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
use dbreps2::{linker, str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
    cat_pages: u64,
    cat_subcats: u64,
}

pub struct SelfCatCats {}

impl Report<Row> for SelfCatCats {
    fn title(&self) -> &'static str {
        "Self-categorized categories"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* selfcatcats.rs SLOW_OK */
SELECT
  page_title,
  cat_pages,
  cat_subcats
FROM page
JOIN categorylinks
ON cl_to = page_title
RIGHT JOIN category
ON cat_title = page_title
WHERE page_id = cl_from
AND page_namespace = 14;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |(page_title, cat_pages, cat_subcats)| {
                Row {
                    page_title,
                    cat_pages,
                    cat_subcats,
                }
            })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Category", "Members", "Subcategories"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![linker(14, &row.page_title), row.cat_pages, row.cat_subcats]
    }

    fn code(&self) -> &'static str {
        include_str!("selfcatcats.rs")
    }
}
