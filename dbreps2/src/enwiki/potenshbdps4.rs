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
select
  page_title,
  cl_to
from
  page as p1
  join categorylinks on cl_from = p1.page_id
where
  p1.page_namespace = 0
  and cl_to like ?
  and not exists (
    select
      *
    from
      page AS p2
      join categorylinks on p2.page_id = cl_from
    where
      p2.page_title = p1.page_title
      and p2.page_namespace = 0
      and (cl_to like "%_deaths" or cl_to = "Year_of_death_unknown" or cl_to = "Year_of_death_missing")
  );
"#
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
