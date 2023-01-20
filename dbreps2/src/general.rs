/*
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
mod articlesmostredirects;
mod blankpages;
mod excessiveips;
mod excessiveusers;
mod indeffullredirects;
mod indefips;
mod linkedemailsinarticles;
mod linkedredlinkedcats;
mod oldeditors;
mod ownerlessuserpages;
mod pollcats;
mod uncatcats;
mod uncattemps;
mod userlinksinarticles;

pub use {
    articlesmostredirects::ArticlesMostRedirects, blankpages::BlankPages,
    excessiveips::ExcessiveIps, excessiveusers::ExcessiveUsers,
    indeffullredirects::IndefFullRedirects, indefips::IndefIPs,
    linkedemailsinarticles::LinkedEmailsInArticles,
    linkedredlinkedcats::LinkedRedlinkedCats, oldeditors::OldEditors,
    ownerlessuserpages::Ownerlessuserpages, pollcats::Pollcats,
    uncatcats::UncatCats, uncattemps::UncatTemps,
    userlinksinarticles::UserLinksInArticles,
};
