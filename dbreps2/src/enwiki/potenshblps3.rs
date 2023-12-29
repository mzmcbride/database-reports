/*
Copyright 2009, 2013 bjweeks, MZMcBride, Tim Landscheidt
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

pub struct Potenshblps3 {}

impl Report<Row> for Potenshblps3 {
    fn title(&self) -> &'static str {
        "Potential biographies of living people (3)"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r"
/* potenshblps3.rs SLOW_OK */
SELECT
  pg1.page_title
FROM
  page AS pg1
  JOIN templatelinks ON pg1.page_id = tl_from
  JOIN linktarget ON tl_target_id = lt_id
WHERE
  lt_namespace = 10
  AND lt_title = 'BLP'
  AND pg1.page_namespace = 1
  AND NOT EXISTS(
    SELECT
      1
    FROM
      page AS pg2
      JOIN categorylinks ON pg2.page_id = cl_from
    WHERE
      pg1.page_title = pg2.page_title
      AND pg2.page_namespace = 0
      AND (
        cl_to IN (
          'Living_people',
          'Possibly_living_people',
          'Human_name_disambiguation_pages',
          'Missing_people'
        )
        OR cl_to LIKE 'Musical_groups%'
        OR cl_to LIKE '%music_groups'
      )
  )
  AND NOT EXISTS(
    SELECT
      1
    FROM
      page AS pg6
      JOIN categorylinks ON pg6.page_id = cl_from
    WHERE
      pg1.page_title = pg6.page_title
      AND pg6.page_namespace = 1
      AND cl_to = 'Musicians_work_group_articles'
  )
  AND NOT EXISTS(
    SELECT
      1
    FROM
      page AS pg7
    WHERE
      pg1.page_title = pg7.page_title
      AND pg7.page_namespace = 0
      AND pg7.page_is_redirect = 1
  )
  AND EXISTS(
    SELECT
      1
    FROM
      page AS pg8
      JOIN templatelinks ON pg8.page_id = tl_from
      JOIN linktarget ON tl_target_id = lt_id
    WHERE
      lt_namespace = 10
      AND lt_title = 'WikiProject_Biography'
      AND pg1.page_title = pg8.page_title
      AND pg8.page_namespace = 1
  )
  AND REPLACE(pg1.page_title, '_', ' ') NOT REGEXP '(^List of|^Line of|\bcontroversy\b|\belection\b|\bmurder(s)?\b|\binvestigation\b|\bkidnapping\b|\baffair\b|\ballegation\b|\brape(s)?\b| v. |\bfamily\b| and |\bband\b| of |\barchive\b|recordholders| & |^The|^[0-9]|\bfiction\b|\bcharacter\b| the |\bincident(s)?\b|\bprinciples\b|\bmost\b)'
LIMIT
  1000;
"
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let rows = conn
            .query_map(self.query(), |page_title| Row { page_title })
            .await?;
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Articles whose talk pages transclude {{tl|BLP}} that are likely to be \
        biographies of living people, but are not in [[:Category:Living people]], \
        [[:Category:Possibly living people]], or [[:Category:Missing people]] \
        (limited to the first 1000 entries)"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title)]
    }

    fn code(&self) -> &'static str {
        include_str!("potenshblps3.rs")
    }
}
