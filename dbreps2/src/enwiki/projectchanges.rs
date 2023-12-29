/*
Copyright 2009-2010 bjweeks, MZMcBride, svick
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
    project: String,
    count: u32,
    no_bots_count: u32,
    // For some reason this subquery is NULL sometimes
    page_is_redirect: Option<u32>,
}

pub struct ProjectChanges {}

impl Report<Row> for ProjectChanges {
    fn title(&self) -> &'static str {
        "WikiProjects by changes"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r"
/* projectchanges.rs SLOW_OK */
SELECT
  SUBSTRING_INDEX(page_title, '/', 1) AS project,
  SUM(
    (
      SELECT
        COUNT(*)
      FROM
        revision
      WHERE
        page_id = rev_page
        AND DATEDIFF(NOW(), rev_timestamp) <= 365
    )
  ) AS count,
  SUM(
    (
      SELECT
        COUNT(*)
      FROM
        revision_userindex
      WHERE
        page_id = rev_page
        AND DATEDIFF(NOW(), rev_timestamp) <= 365
        AND rev_actor NOT IN (
          SELECT
            actor_id
          FROM
            user_groups
            JOIN user ON user_id = ug_user
            JOIN actor ON actor_user = user_id
          WHERE
            ug_group = 'bot'
        )
    )
  ) AS no_bots_count,
  (
    SELECT
      page_is_redirect
    FROM
      page
    WHERE
      page_namespace = 4
      AND page_title = project
  ) AS redirect
FROM
  page
WHERE
  (
    page_title LIKE 'WikiProject\_%'
    OR page_title LIKE 'WikiAfrica'
  )
  AND page_namespace BETWEEN 4
  AND 5
  AND page_is_redirect = 0
GROUP BY
  project
ORDER BY
  count DESC
"
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(
                self.query(),
                |(project, count, no_bots_count, page_is_redirect)| Row {
                    project,
                    count,
                    no_bots_count,
                    page_is_redirect,
                },
            )
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "List of the active or inactive [[WikiProjects]] by number of changes to all its pages in the last 365 days"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["WikiProject", "Edits", "excl. bots"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        let page = if row.page_is_redirect.unwrap_or(0) == 1 {
            format!("''[[Project:{}|]]''", &row.project)
        } else {
            format!("[[Project:{}|]]", &row.project)
        };
        str_vec![page, row.count, row.no_bots_count]
    }

    fn code(&self) -> &'static str {
        include_str!("projectchanges.rs")
    }
}
