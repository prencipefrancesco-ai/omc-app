{\rtf1\ansi\ansicpg1252\cocoartf2868
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\froman\fcharset0 Times-Roman;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\deftab720
\pard\pardeftab720\partightenfactor0

\f0\fs24 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 # SOP: ARCHITETTURA E LOGICA DEL SISTEMA "OMC"\
\
## 1. MAPPATURA DEI PROCESSI (Core Logic)\
L'agente deve orchestrare il flusso dati seguendo la gerarchia definita nel "Processo OMC":\
- **Forecast Commerciale (Input Primario)**: Origine di ogni previsione di cassa.\
- **Ciclo Attivo**: Generato dalla chiusura delle opportunit\'e0 (Fatturazione Elettronica/Proforma).\
- **Ciclo Passivo**: Costi diretti associati alle commesse/progetti.\
- **Costi Indiretti**: Costi di struttura (affitti, stipendi, utilities) da spalmare sul cash flow.\
\
## 2. REGOLE DI ORCHESTRAZIONE (Decision Making)\
Quando l'utente richiede un'analisi o un inserimento, Antigravity deve:\
1. **Identificare l'Attore**: Verificare se l'azione appartiene a Account, PM, Amministrazione o Admin.\
2. **Validazione Incrociata**: Ogni entrata nel Ciclo Attivo deve avere una corrispondenza (o un alert) rispetto al Forecast iniziale.\
3. **Calcolo Margine**: Il sistema deve sottrarre dal Ciclo Attivo sia i costi del Ciclo Passivo che la quota parte dei Costi Indiretti per determinare l'Utile Netto.\
\
## 3. ESECUZIONE DETERMINISTICA (Python Scripts)\
L'agente non deve calcolare i saldi "a mente". Deve scrivere ed eseguire script in `execution/` per:\
- `calc_cashflow.py`: Somma algebrica di Saldo Iniziale + Entrate (Attivo) - Uscite (Passivo + Indiretti).\
- `forecast_engine.py`: Analisi della pipeline commerciale per generare lo scenario "Expected".\
- `margin_analysis.py`: Calcolo della marginalit\'e0 per singolo cliente/commessa.\
\
## 4. GESTIONE STATI (State Machine)\
Il sistema deve gestire gli stati del denaro per garantire previsioni accurate:\
- **STATO 0 (Forecast)**: Solo probabilit\'e0 commerciale.\
- **STATO 1 (Ordered)**: Ordine ricevuto, incasso certo ma non ancora fatturato.\
- **STATO 2 (Invoiced)**: Fattura emessa, data di scadenza definita.\
- **STATO 3 (Paid)**: Liquidit\'e0 effettiva in banca.\
\
## 5. REQUISITI DI OUTPUT (Deliverables)\
Ogni analisi deve produrre:\
- Un file temporaneo in `.tmp/` per il debug.\
- Un aggiornamento del database centrale.\
- Una visualizzazione grafica (Dashboard) che mostri chiaramente lo scostamento tra Forecast e Reale.}