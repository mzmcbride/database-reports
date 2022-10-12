/*
Copyright 2008 bjweeks, MZMcBride
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
use log::info;
use mwapi::Client;

pub async fn exists(client: &Client, title: &str) -> Result<bool> {
    let resp = client
        .get_value(&[("action", "query"), ("titles", title)])
        .await?;
    Ok(!resp["query"]["pages"][0]["missing"]
        .as_bool()
        .unwrap_or_default())
}

pub async fn get_wikitext(client: &Client, title: &str) -> Result<String> {
    let resp = client
        .get_value(&[
            ("action", "query"),
            ("titles", title),
            ("prop", "revisions"),
            ("rvprop", "content"),
            ("rvslots", "main"),
        ])
        .await?;
    Ok(
        resp["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
            .as_str()
            .map(|t| t.to_string())
            .unwrap_or_default(),
    )
}

pub async fn save_page(client: &Client, title: &str, text: &str) -> Result<()> {
    info!("Updating [[{}]]", &title);
    info!("{}", &text);
    client
        .post_with_token(
            "csrf",
            &[
                ("action", "edit"),
                ("title", title),
                ("text", text),
                ("summary", "Bot: updating database report"),
            ],
        )
        .await?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_get_wikitext() {
        let client = Client::new("https://en.wikipedia.org/w/api.php")
            .await
            .unwrap();
        let wikitext = get_wikitext(&client, "Project:Database reports")
            .await
            .unwrap();
        assert!(wikitext.contains("'''Database reports''' query"));
        let wikitext2 =
            get_wikitext(&client, "This page does not exist at all")
                .await
                .unwrap();
        assert!(wikitext2.is_empty());
    }

    #[tokio::test]
    async fn test_exists() {
        let client = Client::new("https://en.wikipedia.org/w/api.php")
            .await
            .unwrap();
        assert!(exists(&client, "Taylor Swift").await.unwrap());
        assert!(!exists(&client, "This page does not exist").await.unwrap());
    }
}
