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
use dbreps2::{escape_reason, str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    ipb_address: String,
    actor_name: String,
    ipb_timestamp: String,
    ipb_expiry: String,
    comment_text: String,
}

pub struct ExcessiveUsers {}

#[async_trait::async_trait]
impl Report<Row> for ExcessiveUsers {
    fn title(&self) -> &'static str {
        "Unusually long user blocks"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Monthly
    }

    fn query(&self) -> &'static str {
        r#"
/* excessiveusers.rs SLOW_OK */
SELECT
  ipb_address,
  actor_name,
  ipb_timestamp,
  ipb_expiry,
  comment_text
FROM
  ipblocks
  INNER JOIN actor_ipblocks ON ipb_by_actor = actor_id
  INNER JOIN comment_ipblocks ON ipb_reason_id = comment_id
WHERE
  ipb_expiry > DATE_FORMAT(DATE_ADD(NOW(), INTERVAL 2 YEAR), '%Y%m%d%H%i%s')
  AND ipb_expiry != "infinity"
  AND ipb_user != 0;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(
                    ipb_address,
                    actor_name,
                    ipb_timestamp,
                    ipb_expiry,
                    comment_text,
                )| Row {
                    ipb_address,
                    actor_name,
                    ipb_timestamp,
                    ipb_expiry,
                    comment_text,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Unusually long (more than two years) blocks of users"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["User", "Admin", "Timestamp", "Expiry", "Reason"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("{{{{User|1={}}}}}", &row.ipb_address),
            format!("[[User talk:{}|]]", &row.actor_name),
            row.ipb_timestamp,
            row.ipb_expiry,
            escape_reason(&row.comment_text)
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("excessiveusers.rs")
    }
}
