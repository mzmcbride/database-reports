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
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
}

pub struct LinkedEmailsInArticles {}

#[async_trait::async_trait]
impl Report<Row> for LinkedEmailsInArticles {
    fn title(&self) -> &'static str {
        "Articles containing linked e-mail addresses"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* linkedemailsinarticles.rs SLOW_OK */
SELECT
  DISTINCT page_title
FROM
  externallinks
  JOIN page ON el_from = page_id
WHERE
  el_index_60 LIKE 'mailto:%'
  AND page_namespace = 0
LIMIT
  1000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("linkedemailsinarticles.rs")
    }
}
