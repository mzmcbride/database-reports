use anyhow::Result;
use dbreps2::Report;
use log::info;
use mysql_async::Pool;

mod general;

macro_rules! run_general {
    ( $client:expr, $pool:expr, $( $x:ident ),* ) => {
        $(
            let report = general::$x {};
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
    run_general!(
        &enwiki_api,
        &enwiki_db,
        ExcessiveIps,
        IndefFullRedirects,
        UncatCats
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
    run_general!(&commonswiki_api, &commonswiki_db, ExcessiveIps);
    // Cleanup
    commonswiki_db.disconnect().await?;

    Ok(())
}
