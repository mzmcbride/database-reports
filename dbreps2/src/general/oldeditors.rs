/*
Copyright Thparkth, MaxSem
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
    user_name: String,
    user_registration: String,
    user_editcount: u32,
}

pub struct OldEditors {}

#[async_trait::async_trait]
impl Report<Row> for OldEditors {
    fn title(&self) -> &'static str {
        "Active editors with the longest-established accounts"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn query(&self) -> &'static str {
        r#"
/* oldeditors.rs SLOW_OK */
SELECT
  user_name,
  user_registration,
  user_editcount
FROM
  (
    SELECT
      user_name,
      user_registration,
      user_editcount
    FROM
      user
    WHERE
      user_id IN (
        SELECT
          DISTINCT actor_user
        FROM
          actor_recentchanges
        WHERE
          actor_user > 0
      )
      AND user_registration IS NOT NULL
    ORDER BY
      user_id
    LIMIT
      250
  ) AS InnerQuery
ORDER BY
  user_registration
LIMIT
  200
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(user_name, user_registration, user_editcount)| Row {
                    user_name,
                    user_registration,
                    user_editcount,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "The 200 earliest-created editor accounts that have been active in the last thirty days"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Username", "Account creation", "Approx. edit count"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("[[User:{}|]]", &row.user_name),
            row.user_registration,
            row.user_editcount
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("oldeditors.rs")
    }
}
