/*
Copyright 2011 MZMcBride
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
use dbreps2::{str_vec, Frequency, Report};
use log::{debug, info};
use mwbot::{Bot, SaveOptions};
use mysql_async::prelude::*;
use mysql_async::Conn;
use std::collections::HashSet;
use thousands::Separable;

async fn get_user_list(conn: &mut Conn, page: &str) -> Result<HashSet<String>> {
    debug!("Getting user list: {}", page);
    let rows: Vec<String> = conn
        .exec_map(
            r#"
/* editcount.rs SLOW_OK */
SELECT DISTINCT
 lt_title
FROM page
JOIN pagelinks
ON pl_from = page_id
JOIN linktarget on pl_target_id = lt_id
WHERE page_title = ?
AND page_namespace = 4
AND lt_namespace IN (2,3);
"#,
            (page,),
            |(lt_title,)| lt_title,
        )
        .await?;
    Ok(rows
        .into_iter()
        .map(|name| name.replace('_', " "))
        .collect())
}

async fn get_bot_list(conn: &mut Conn) -> Result<HashSet<String>> {
    debug!("Getting bot list");
    let rows: Vec<String> = conn
        .query_map(
            r#"
/* editcount.rs SLOW_OK */
SELECT
 user_name
FROM user
JOIN user_groups
ON user_id = ug_user
WHERE ug_group = 'bot';
"#,
            |(user_name,)| user_name,
        )
        .await?;
    Ok(rows
        .into_iter()
        .map(|name| name.replace('_', " "))
        .collect())
}

async fn get_user_groups(conn: &mut Conn, username: &str) -> Result<String> {
    debug!("Fetching user groups for {}", username);
    let mut rows: Vec<String> = conn
        .exec_map(
            r#"
/* editcount.rs SLOW_OK */
SELECT
 ug_group
FROM user_groups
JOIN user
ON user_id = ug_user
WHERE user_name = ?;
"#,
            (username,),
            |(ug_group,)| ug_group,
        )
        .await?;
    rows.sort();
    let formatted: Vec<_> = rows
        .into_iter()
        .map(|group| format!("{{{{subst:aug|1={group}}}}}"))
        .collect();
    Ok(formatted.join(", "))
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

struct UserRow {
    user_name: String,
    user_editcount: u64,
}

pub struct Row {
    name: String,
    editcount: u64,
    groups: String,
    is_active: bool,
}

pub struct EditCount {}

impl Report<Row> for EditCount {
    fn title(&self) -> &'static str {
        "<placeholder>"
    }

    fn get_title(&self) -> String {
        "Wikipedia:List of Wikipedians by number of edits".to_string()
    }

    fn frequency(&self) -> Frequency {
        Frequency::Daily
    }

    fn rows_per_page(&self) -> Option<usize> {
        Some(1000)
    }

    fn query(&self) -> &'static str {
        r#"
/* editcount.rs SLOW_OK */
SELECT
  user_name,
  user_editcount
FROM user
WHERE user_editcount > 0
ORDER BY user_editcount DESC
LIMIT 12000;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let unflagged_bots = get_user_list(
            conn,
            "List_of_Wikipedians_by_number_of_edits/Unflagged_bots",
        )
        .await?;
        let flagged_bots = get_bot_list(conn).await?;
        let opt_out = get_user_list(
            conn,
            "List_of_Wikipedians_by_number_of_edits/Anonymous",
        )
        .await?;
        let mut processed: usize = 0;
        let mut formatted = vec![];
        debug!("Starting main query...");
        let rows = conn
            .query_map(self.query(), |(user_name, user_editcount)| UserRow {
                user_name,
                user_editcount,
            })
            .await?;
        debug!("Finished main query!");
        for row in rows {
            if unflagged_bots.contains(&row.user_name)
                || flagged_bots.contains(&row.user_name)
            {
                continue;
            }
            let (formatted_name, groups, is_active) =
                if opt_out.contains(&row.user_name) {
                    ("[Placeholder]".to_string(), "".to_string(), false)
                } else {
                    let groups = get_user_groups(conn, &row.user_name).await?;
                    let is_active = is_active(conn, &row.user_name).await?;
                    (row.user_name, groups, is_active)
                };
            formatted.push(Row {
                name: formatted_name,
                editcount: row.user_editcount,
                groups,
                is_active,
            });
            processed += 1;
            if processed >= 10000 {
                break;
            }
        }
        Ok(formatted)
    }

    fn intro(&self) -> &'static str {
        ""
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["User", "Edit count", "User groups"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            if row.is_active {
                format!("[[User:{}|{}]]", &row.name, &row.name)
            } else {
                row.name.to_string()
            },
            row.editcount.separate_with_commas(),
            row.groups
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("editcount.rs")
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
! User groups
"#,
            index_to_range(index)
        )
    }

    fn get_footer(&self) -> String {
        "|-\n|}\n".to_string()
    }

    fn title_for_update_check(&self) -> String {
        "Wikipedia:List of Wikipedians by number of edits/Age".to_string()
    }

    async fn post_run(&self, bot: &Bot, debug_mode: bool) -> Result<()> {
        info!("Updating Wikipedia:List of Wikipedians by number of edits/Age");

        if !debug_mode {
            bot.page("Wikipedia:List of Wikipedians by number of edits/Age")?
                .save(
                    "<onlyinclude>~~~~~</onlyinclude>",
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
