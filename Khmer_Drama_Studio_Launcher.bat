@echo off
title Khmer AI Drama Voice Translator & Movie Recap Studio (Piseth & Sreymom)
cd /d "%~dp0"

echo ================================================================
echo  🎬 Khmer AI Drama Voice Translator & Movie Recap Studio
echo  🎙️ សំឡេងខ្មែរ AI ផ្លូវការ: ពិសិដ្ឋ (Piseth) & ស្រីមុំ (Sreymom)
echo ================================================================
echo.
echo កំពុងចាប់ផ្តើមដំណើរការកម្មវិធី... សូមរង់ចាំបន្តិច!
echo.

python desktop_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo កំពុងបើកតាមរយៈ Web Launcher ជំនួសវិញ...
    python run_studio.py
)

pause
