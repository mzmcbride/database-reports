use anyhow::Result;
use dbreps2::Report;
use log::info;
use mysql_async::Pool;

mod enwiki;
mod general;

macro_rules! run {
    ( $client:expr, $pool:expr, $( $x:expr ),* ) => {
        $(
            let report = $x;
            report.run($client, $pool).await?;
        )*
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();
    let cfg = dbreps2::load_config().await?;
    /* enwiki reports */
    let enwiki_api =
        mwapi::Client::bot_builder("https://en.wikipedia.org/w/api.php")
            .set_botpassword(&cfg.auth.username, &cfg.auth.password)
            .build()
            .await?;
    info!("Setting up MySQL connection pool for enwiki...");
    let enwiki_db = Pool::new(
        toolforge::connection_info!("enwiki", ANALYTICS)?.to_string(),
    );
    run!(
        &enwiki_api,
        &enwiki_db,
        general::ExcessiveIps {},
        general::IndefFullRedirects {},
        general::LinkedEmailsInArticles {},
        general::OldEditors {},
        general::Pollcats {},
        general::UncatCats {},
        general::UserLinksInArticles {},
        enwiki::BrokenWikiProjTemps {},
        enwiki::ConflictedFiles {},
        enwiki::EmptyCats {},
        enwiki::LinkedMiscapitalizations {},
        enwiki::LinkedMisspellings {},
        enwiki::LongStubs {},
        enwiki::LotNonFree {},
        enwiki::NewProjects {},
        enwiki::OldDeletionDiscussions {},
        enwiki::OrphanedAfds {},
        enwiki::OrphanedSubTalks {},
        enwiki::OverusedNonFree {},
        enwiki::PollTemps {},
        enwiki::Potenshbdps1 {},
        enwiki::Potenshbdps3 {},
        enwiki::Potenshblps1 {},
        enwiki::Potenshblps2 {},
        enwiki::Potenshblps3 {},
        enwiki::ProjectChanges {},
        enwiki::ShortestBios {},
        enwiki::StickyProdBLPs {},
        enwiki::TemplateDisambigs {},
        enwiki::TemplatesNonFree {},
        enwiki::UnbelievableLifeSpans {},
        enwiki::UncatUnrefBLPs {},
        enwiki::UnsourcedBLPs {},
        enwiki::UntaggedBLPs {},
        enwiki::UntaggedStubs {},
        enwiki::UntaggedUnrefBLPs {},
        enwiki::UnusedNonFree {},
        enwiki::UserCats {}
    );
    // Cleanup
    enwiki_db.disconnect().await?;

    /* commonswiki reports */
    let commonswiki_api =
        mwapi::Client::bot_builder("https://commons.wikimedia.org/w/api.php")
            .set_botpassword(&cfg.auth.username, &cfg.auth.password)
            .build()
            .await?;
    info!("Setting up MySQL connection pool for commonswiki...");
    let commonswiki_db = Pool::new(
        toolforge::connection_info!("commonswiki", ANALYTICS)?.to_string(),
    );
    run!(&commonswiki_api, &commonswiki_db, general::ExcessiveIps {});
    // Cleanup
    commonswiki_db.disconnect().await?;

    Ok(())
}
