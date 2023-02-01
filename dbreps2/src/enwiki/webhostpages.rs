/*
Copyright 2022 MZMcBride
Copyright 2022 Kunal Mehta <legoktm@debian.org>

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
    user_name: String,
    page_len: u64,
    page_id: u64,
    user_editcount: u64,
}

pub struct WebhostPages {}

#[async_trait::async_trait]
impl Report<Row> for WebhostPages {
    fn title(&self) -> &'static str {
        "Potential U5s"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(3000)
    }

    fn static_row_numbers(&self) -> bool {
        true
    }

    fn query(&self) -> &'static str {
        r#"
/* webhostpages.rs SLOW_OK */
SELECT
  user_name,
  page_len,
  page_id,
  user_editcount
FROM
  user
  JOIN page ON page_title = REPLACE(user_name, ' ', '_')
  AND page_namespace = 2
WHERE
  page_len > 499
  AND page_id < 58000000
  AND (
    SELECT
      COUNT(*)
    FROM
      revision_userindex
      JOIN actor ON actor_id = rev_actor
      JOIN page ON rev_page = page_id
    WHERE
      actor_name = user_name
      AND page_namespace IN (2, 3)
  ) = user_editcount
ORDER BY
  user_id DESC
LIMIT
  21000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(user_name, page_len, page_id, user_editcount)| Row {
                    user_name,
                    page_len,
                    page_id,
                    user_editcount,
                },
            )
            .await?;
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Length", "Page ID", "Edit count"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            linker(2, &row.user_name),
            row.page_len,
            row.page_id,
            row.user_editcount
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("webhostpages.rs")
    }
}
