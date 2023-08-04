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
use dbreps2::{str_vec, Frequency, Report};
use mysql_async::prelude::*;
use mysql_async::Conn;

pub struct Row {
    page_title: String,
}

pub struct UserLinksInArticles {}

#[async_trait::async_trait]
impl Report<Row> for UserLinksInArticles {
    fn title(&self) -> &'static str {
        "Articles containing links to the user space"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* userlinksinarticles.rs SLOW_OK */
SELECT
  DISTINCT page_title
FROM
  page
  JOIN pagelinks ON pl_from = page_id
WHERE
  pl_from_namespace = 0
  AND pl_namespace IN (2, 3)
  AND NOT EXISTS (
    SELECT 1 FROM templatelinks
    JOIN linktarget ON tl_target_id = lt_id
    WHERE tl_from = page_id
    AND lt_namespace = 10
    AND lt_title IN (
      'Db-meta',
      'Under_construction',
      'GOCEinuse',
      'Proposed_deletion/dated',
      'Wikipedia_person_user_link',
      'Cleanup_bare_URLs'
    )
  );
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let mut rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        rows.sort_by(|a, b| a.page_title.cmp(&b.page_title));
        Ok(rows)
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Article"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title.replace('_', " "))]
    }

    fn code(&self) -> &'static str {
        include_str!("userlinksinarticles.rs")
    }
}
