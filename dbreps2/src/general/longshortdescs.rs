/*
Forked from <https://quarry.wmcloud.org/query/82687>.

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
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::{prelude::Queryable, Conn};

pub struct Row {
    page_title: String,
    pp_value: String,
    length: usize,
}

pub struct LongShortDescs;

impl Report<Row> for LongShortDescs {
    fn title(&self) -> &'static str {
        "Long short descriptions"
    }

    fn intro(&self) -> &'static str {
        "Pages with short descriptions that are longer than 100 characters"
    }

    fn query(&self) -> &'static str {
        "
SELECT
  page_title,
  pp_value,
  CHAR_LENGTH(pp_value)
FROM
  page_props
  JOIN page ON pp_page = page_id
WHERE
  page_namespace = 0
  AND pp_propname = 'wikibase-shortdesc'
  AND CHAR_LENGTH(pp_value) >= 100;
"
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let mut rows = conn
            .query_map(self.query(), |(page_title, pp_value, length)| Row {
                page_title,
                pp_value,
                length,
            })
            .await?;
        rows.sort_by_key(|row| row.length);
        rows.reverse();
        Ok(rows)
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title), row.pp_value, row.length]
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Short description", "Length"]
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn code(&self) -> &'static str {
        include_str!("longshortdescs.rs")
    }
}
