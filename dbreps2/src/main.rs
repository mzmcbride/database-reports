use anyhow::Result;
use dbreps2::Report;
use log::info;
use mysql_async::Pool;

mod general;

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::Builder::from_env(
        env_logger::Env::default().default_filter_or("info"),
    )
    .init();
    let cfg = dbreps2::load_config().await?;
    let client =
        mwapi::Client::bot_builder("https://en.wikipedia.org/w/api.php")
            .set_botpassword(&cfg.auth.username, &cfg.auth.password)
            .build()
            .await?;
    info!("Setting up MySQL connection pool...");
    let db_url = toolforge::connection_info!("enwiki", ANALYTICS)?;
    let pool = Pool::new(db_url.to_string());
    // Reports to run
    let report = general::uncatcats::UncatCats {};
    report.run(&client, &pool).await?;
    let report = general::indeffullredirects::IndefFullRedirects {};
    report.run(&client, &pool).await?;

    // Cleanup
    pool.disconnect().await?;
    Ok(())
}
