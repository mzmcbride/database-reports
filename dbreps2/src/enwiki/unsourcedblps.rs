/*
Copyright 2011, 2013 bjweeks, MZMcBride, WOSlinker, Tim Landscheidt
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

pub struct UnsourcedBLPs {}

impl Report<Row> for UnsourcedBLPs {
    fn title(&self) -> &'static str {
        "Biographies of living people containing unsourced statements"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* unsourcedblps.rs SLOW_OK */
SELECT
  page_title
FROM
  page
  JOIN templatelinks ON tl_from = page_id
  JOIN linktarget ON tl_target_id = lt_id
  JOIN categorylinks ON cl_from = page_id
WHERE
  cl_to = 'Living_people'
  AND lt_namespace = 10
  AND lt_title = 'Citation_needed'
  AND page_namespace = 0
LIMIT
  500;
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "{{NOINDEX}}{{shortcut|WP:DR/BLP}}\nPages in [[:Category:Living people]] that \
        [[Special:WhatLinksHere/Template:Citation needed|transclude]] \
        [[Template:Citation needed]] (limited to the first 500 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Article"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("{{{{ple|1={}}}}}", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("unsourcedblps.rs")
    }
}
