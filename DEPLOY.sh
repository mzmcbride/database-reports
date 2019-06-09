echo Deploying changes to toolsforge.
cd $HOME/src/database-reports
git pull
python setup.py install --user --install-scripts ~/bin
echo Done. Crons are not updated automatically.
