/*
Copyright 2011 MZMcBride
Copyright 2022-2023 Kunal Mehta <legoktm@debian.org>

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
use log::{debug, info};
use mwbot::{Bot, SaveOptions};
use mysql_async::prelude::*;
use mysql_async::Conn;
use std::collections::HashMap;
use thousands::Separable;

async fn get_user_list(
    conn: &mut Conn,
    page: &str,
) -> Result<HashMap<String, u64>> {
    debug!("Getting user list: {}", page);
    let rows = conn
        .exec_map(
            r#"
/* editcount.rs SLOW_OK */
SELECT
 user_name,
 user_editcount
FROM page
JOIN pagelinks
ON pl_from = page_id
JOIN user
ON user_name = REPLACE(pl_title, "_", " ")
WHERE page_title = ?
AND page_namespace = 4
AND pl_namespace IN (2,3);
"#,
            (page,),
            |(user_name, user_editcount)| (user_name, user_editcount),
        )
        .await?
        .into_iter()
        .collect();
    Ok(rows)
}

async fn get_bot_list(conn: &mut Conn) -> Result<HashMap<String, u64>> {
    debug!("Getting bot list");
    let rows = conn
        .query_map(
            r#"
/* editcount.rs SLOW_OK */
SELECT
 user_name,
 user_editcount
FROM user
JOIN user_groups
ON user_id = ug_user
WHERE ug_group = 'bot';
"#,
            |(user_name, user_editcount)| (user_name, user_editcount),
        )
        .await?
        .into_iter()
        .collect();
    Ok(rows)
}

async fn is_active(conn: &mut Conn, username: &str) -> Result<bool> {
    debug!("Fetching activity level for {}", username);
    let rows: Vec<usize> = conn
        .exec_map(
            r#"
/* editcount.rs SLOW_OK */
SELECT
  1
FROM
  recentchanges_userindex
  JOIN actor ON rc_actor = actor_id
WHERE
  actor_name = ?
LIMIT 1
"#,
            (username,),
            |(one,)| one,
        )
        .await?;
    Ok(rows.len() == 1)
}

pub struct Row {
    name: String,
    editcount: u64,
    is_active: bool,
}

pub struct BotEditCount {}

#[async_trait::async_trait]
impl Report<Row> for BotEditCount {
    fn title(&self) -> &'static str {
        "<boteditcount>"
    }

    fn get_title(&self) -> String {
        "Wikipedia:List of bots by number of edits".to_string()
    }

    fn frequency(&self) -> Frequency {
        Frequency::DailyAt(5)
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(1000)
    }

    fn query(&self) -> &'static str {
        r#""#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let mut bots = get_bot_list(conn).await?;
        bots.extend(
            get_user_list(
                conn,
                "List_of_Wikipedians_by_number_of_edits/Unflagged_bots",
            )
            .await?,
        );
        let mut formatted = vec![];
        for (username, editcount) in bots {
            let is_active = is_active(conn, &username).await?;
            formatted.push(Row {
                name: username,
                editcount,
                is_active,
            });
        }
        formatted.sort_by_key(|row| row.editcount);
        formatted.reverse();
        Ok(formatted)
    }

    fn intro(&self) -> &'static str {
        ""
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["User", "Edit count"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            if row.is_active {
                format!("[[User:{}|{}]]", &row.name, &row.name)
            } else {
                row.name.to_string()
            },
            row.editcount.separate_with_commas()
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("boteditcount.rs")
    }

    fn get_intro(&self, index: usize) -> String {
        format!(
            r#"
=== {} ===
{{| class="wikitable"
|- style="white-space:nowrap;"
! No.
! User
! Edit count
"#,
            index_to_range(index)
        )
    }

    fn get_footer(&self) -> String {
        "|-\n|}\n".to_string()
    }

    fn needs_update(&self, _old_text: &str) -> Result<bool> {
        Ok(time::OffsetDateTime::now_utc().hour() == 4)
    }

    async fn post_run(&self, bot: &Bot, debug_mode: bool) -> Result<()> {
        info!("Updating Wikipedia:List of bots by number of edits/Age");

        if !debug_mode {
            bot.page("Wikipedia:List of bots by number of edits/Age")?
                .save(
                    "~~~~~",
                    &SaveOptions::summary("[[WP:BOT|Bot]]: Updated page."),
                )
                .await?;
        }
        Ok(())
    }

    fn subpage(&self, index: usize) -> String {
        format!("{}/{}", self.get_title(), index_to_range(index))
    }

    fn update_index(&self) -> bool {
        false
    }
}

fn index_to_range(index: usize) -> String {
    let start = ((index - 1) * 1000) + 1;
    let end = start + 999;
    format!("{start}–{end}")
}

#[test]
fn test_index_to_range() {
    assert_eq!(&index_to_range(1), "1–1000");
    assert_eq!(&index_to_range(2), "1001–2000");
}
