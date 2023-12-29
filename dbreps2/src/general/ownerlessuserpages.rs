/*
Copyright 2008 bjweeks, MZMcBride
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

struct FirstRow {
    page_id: u64,
    page_namespace: u32,
    page_title: String,
    page_len: u64,
}

struct SecondRow {
    rev_timestamp: String,
    actor_name: String,
}

pub struct Row {
    page_namespace: u32,
    page_title: String,
    length: u64,
    creator: String,
    creation_date: String,
}

async fn user_exists_globally(ca_conn: &mut Conn, name: &str) -> Result<bool> {
    let row: Option<usize> = ca_conn
        .exec_first(
            r#"
SELECT
1
FROM globaluser
WHERE gu_name = ?
"#,
            (name,),
        )
        .await?;
    Ok(row.is_some())
}

async fn lookup_revision(conn: &mut Conn, row: &FirstRow) -> Result<SecondRow> {
    Ok(conn
        .exec_map(
            r#"
SELECT
  rev_timestamp,
  actor_name
FROM
  page
  JOIN revision ON page_id = rev_page
  JOIN actor ON rev_actor = actor_id
WHERE
  page_id = ?
ORDER BY
  rev_timestamp ASC
LIMIT
  1;
"#,
            (row.page_id,),
            |(rev_timestamp, actor_name)| SecondRow {
                rev_timestamp,
                actor_name,
            },
        )
        .await?
        .into_iter()
        .next()
        .unwrap())
}

pub struct Ownerlessuserpages {}

impl Report<Row> for Ownerlessuserpages {
    fn title(&self) -> &'static str {
        "Ownerless pages in the user space"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Daily
    }

    fn query(&self) -> &'static str {
        r"
/* ownerlessuserpages.rs SLOW_OK */
SELECT
  page_id,
  page_namespace,
  page_title,
  page_len
FROM
  page
  LEFT JOIN user ON user_name = REPLACE(SUBSTRING_INDEX(page_title, '/', 1), '_', ' ')
WHERE
  page_namespace IN (2, 3)
  AND page_is_redirect = 0
  AND NOT IS_IPV4(SUBSTRING_INDEX(page_title, '/', 1))
  AND NOT IS_IPV6(SUBSTRING_INDEX(page_title, '/', 1))
  AND page_title NOT RLIKE '(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
  AND ISNULL(user_name);
"
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(page_id, page_namespace, page_title, page_len)| FirstRow {
                    page_id,
                    page_namespace,
                    page_title,
                    page_len,
                },
            )
            .await?;
        let ca_pool = self.centralauth()?;
        let mut ca_conn = ca_pool.get_conn().await?;
        let mut last = vec![];
        for row in rows {
            let username = row.page_title.replace('_', " ");
            let username = if username.contains('/') {
                let (username, _) = username.split_once('/').unwrap();
                username.to_string()
            } else {
                username
            };
            if user_exists_globally(&mut ca_conn, &username).await? {
                continue;
            }
            let rev = lookup_revision(conn, &row).await?;
            last.push(Row {
                page_namespace: row.page_namespace,
                page_title: row.page_title,
                length: row.page_len,
                creator: rev.actor_name,
                creation_date: rev.rev_timestamp,
            })
        }
        Ok(last)
    }

    fn intro(&self) -> &'static str {
        "Pages in the user space that do not belong to a [[Special:ListUsers|registered user]]"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Length", "Creator", "Creation date"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            linker(row.page_namespace, &row.page_title),
            row.length,
            row.creator,
            row.creation_date
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("ownerlessuserpages.rs")
    }
}
