/*
Copyright 2009, 2013 bjweeks, MZMcBride, Tim Landscheidt
Copyright 2024 Kunal Mehta <legoktm@debian.org>

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
    page_title: String,
    cl_to: String,
}

pub struct Potenshbdps4 {}

impl Report<Row> for Potenshbdps4 {
    fn title(&self) -> &'static str {
        "Potential biographies of dead people (4)"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* potenshbdps4.rs SLOW_OK */
SELECT
  page_title,
  lt1.lt_title
FROM
  page AS p1
  JOIN categorylinks AS cl1 ON cl1.cl_from = p1.page_id
  JOIN linktarget AS lt1 ON cl1.cl_target_id = lt1.lt_id
WHERE
  p1.page_namespace = 0
  AND lt1.lt_namespace = 14
  AND lt1.lt_title LIKE ?
  AND NOT EXISTS (
    SELECT
      1
    FROM
      page AS p2
      JOIN categorylinks AS cl2 ON p2.page_id = cl2.cl_from
      JOIN linktarget AS lt2 ON cl2.cl_target_id = lt2.lt_id
    WHERE
      p2.page_title = p1.page_title
      AND p2.page_namespace = 0
      AND lt2.lt_namespace = 14
      AND (
        lt2.lt_title LIKE '%_deaths'
        OR lt2.lt_title = 'Year_of_death_unknown'
        OR lt2.lt_title = 'Year_of_death_missing'
      )
  );"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let current_year = time::OffsetDateTime::now_utc().year();
        let mut rows = vec![];
        for year in (current_year - 200)..(current_year - 100) {
            let year_rows = conn
                .exec_map(
                    self.query(),
                    (format!("{year}_births"),),
                    |(page_title, cl_to)| Row { page_title, cl_to },
                )
                .await?;
            //dbg!((year, year_rows.len()));
            rows.extend(year_rows);
        }
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Articles in a \"XXXX births\" category from over 100-200 years ago that are not also in a deaths category"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Biography", "Birth category"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![format!("[[{}]]", row.page_title), linker(14, &row.cl_to)]
    }

    fn code(&self) -> &'static str {
        include_str!("potenshbdps4.rs")
    }
}
