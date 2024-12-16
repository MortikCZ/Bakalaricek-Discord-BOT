<div align="center">

<h1>Bakalaricek Discord Bot</h1>

![GitHub License](https://img.shields.io/github/license/MortikCZ/Bakalaricek-Discord-Bot)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/MortikCZ/Bakalaricek-Discord-Bot)
![GitHub last commit](https://img.shields.io/github/last-commit/MortikCZ/Bakalaricek-Discord-Bot)

<p>Discord Bot pro zobrazování suplování, aktuálního rozvrhu a jeho změn z Bakalářů v jazyce Python.</p>

</div>

 #
Tento bot umožňuje skrze [bakapi-v2](https://github.com/MortikCZ/bakapi-v2), komunikovat s Bakaláři API a získavat informace o suplování, dokáže v předem určeném kanálu zobrazovat suplování a rozvrh pro aktuální týden a posílat upozornění na změny v rozvrhu.

## Konfigurace
Ve složce s botem je před jeho prvním spuštěním nutné vytvořit soubor `config.json`.
```json
{
    "bot": {

```json
    {
    "bot": {
        "token": "token bota"
    },
    "bakalari": {
        "username": "přihlašovací jméno do bakalářů",
        "password": "heslo do bakalářů",
        "url": "URL přihlašovací stránky bakalářů"
    },
    "discord": {
        "substitutions_channel_id": kanál pro zobrazení suplování,
        "timetable_channel_id": kanál pro zobrazení rozvrhu,
        "subst_change_channel_id": kanál pro oznámení změn v rozvrhu,
        "subst_change_role_id": role pro oznámení změn v rozvrhu
    }

```
## Changelog
### 0.4
- Nově bot dokáže posílat oznámení jak pro aktuální, tak příští týden.
### 0.3
- Status se nově ukládá do souboru `config.json` a při restartu bota se načte poslední status.
### 0.2
- Přídán embed pro zobrazení rozvrhu pro aktuální den.
- Přídána možnost nastavení statusu bota pomocí příkazu /status <status>
### 0.1
- První release 