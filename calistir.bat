@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Haberci: bulten hazirlaniyor ===
git pull --rebase
if errorlevel 1 goto hata
python otomatik.py %*
if errorlevel 1 goto hata
git add docs bulten veri/pubmed_gorulen.json
git commit -m "Bulten (elle)"
git push
if errorlevel 1 goto hata
echo.
echo Tamam. Birkac dakika sonra: https://mkaya5153-star.github.io/haberci/
pause
exit /b 0
:hata
echo.
echo HATA olustu. Yukaridaki mesaji okuyun (KULLANIM.md - Sorun giderme).
pause
exit /b 1
