/*
Copyright 2023 Kunal Mehta <legoktm@debian.org>

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
use mwbot::Bot;
use mysql_async::prelude::*;
use mysql_async::Conn;
use wikipedia_prosesize::prosesize;

pub struct Row {
    title: String,
    prose_size: u64,
    word_count: u64,
}

pub struct FeaturedBySize {
    pub(crate) bot: Bot,
}

#[async_trait::async_trait]
impl Report<Row> for FeaturedBySize {
    fn title(&self) -> &'static str {
        "Featured articles by size"
    }

    fn frequency(&self) -> Frequency {
        Frequency::Weekly
    }

    fn query(&self) -> &'static str {
        r#"
/* featuredbysize.rs SLOW_OK */
SELECT
  page_title
FROM
  page
  JOIN categorylinks ON cl_from = page_id
WHERE
  cl_to = "Featured_articles"
  AND page_namespace = 0
"#
    }

    async fn run_query(&self, conn: &mut Conn) -> Result<Vec<Row>> {
        let pages: Vec<String> = conn.query(self.query()).await?;
        let mut rows = vec![];
        let mut handles = vec![];
        for title in pages {
            let page = self.bot.page(&title)?;
            handles.push(tokio::spawn(async move {
                let html = page.html().await?;
                let size = prosesize(html);
                Result::<_, anyhow::Error>::Ok((title, size))
            }));
        }
        for handle in handles {
            let (title, size) = handle.await??;
            println!("{title}");
            rows.push(Row {
                title,
                prose_size: size.prose_size(),
                word_count: size.word_count(),
            })
        }
        rows.sort_by_key(|row| row.prose_size);
        rows.reverse();
        Ok(rows)
    }

    fn intro(&self) -> &'static str {
        "Articles in [[:Category:Featured articles]] sorted by prose size"
    }

    fn headings(&self) -> Vec<&'static str> {
        vec!["Page", "Prose size", "Word count"]
    }

    fn format_row(&self, row: &Row) -> Vec<String> {
        str_vec![
            format!("[[{}]]", row.title.replace('_', " ")),
            row.prose_size,
            row.word_count
        ]
    }

    fn code(&self) -> &'static str {
        include_str!("featuredbysize.rs")
    }
}
