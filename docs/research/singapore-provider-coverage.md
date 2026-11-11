# Singapore provider coverage

Researched 2026-11-11. The question: for each sync provider and market data provider this fork ships, could a Singapore resident plausibly use it today? Each one gets a keep or remove verdict.

"Keep" means a Singapore resident can open the upstream account (or call the API) without a foreign address or entity. "Remove" means the provider is tied to another region's banks, regulator or exchange. "Unclear" means the evidence conflicts, or the provider only works through a workaround such as a US company.

Sources are linked inline. Vendor and regulator pages are the primary sources. Where only press or secondary coverage was found, it is marked *(secondary)*. Endpoints marked "probed" were called directly on 2026-11-11.

## Summary

| | Providers |
|---|---|
| **Keep (sync)** | IBKR, SnapTrade, Sharesight, Wise, Coinbase, Kraken, CoinStats, On-chain wallets |
| **Remove (sync)** | Plaid, TrueLayer, Enable Banking, SimpleFIN, Sophtron, FinanceKit, Akahu, Up, Redbark, CoinSpot, Monobank, Fio, Indexa Capital, Questrade, Trade Republic, Trading 212 |
| **Unclear (sync)** | Lunch Flow, Binance (leans remove), Mercury, Brex |
| **Keep (market data)** | Yahoo Finance, Twelve Data, EODHD, Alpha Vantage, Tiingo, Frankfurter, Binance Public, Blockscout, Etherscan, mempool.space, Solana RPC, Jupiter tokens, Polkadot Sidecar, Cosmos REST |
| **Remove (market data)** | Mansa, MFAPI, MOEX, T-Bank (Tinkoff) Invest, RentCast, Realie, Chimnie |

Keyless market data sources that would stay: Yahoo Finance, Frankfurter, Binance Public, Blockscout, mempool.space, Solana RPC, Jupiter tokens, Polkadot Sidecar and Cosmos REST.

Out of scope: `Provider::Openai`, `Provider::Anthropic` and `Provider::Jev` (LLM), `Provider::Stripe` (billing) and `Provider::Github` (release checks). None of them is a financial data source.

## Sync providers (`app/models/*_item.rb`)

| Provider | Code | Region locked to | Verdict | Evidence |
|---|---|---|---|---|
| Interactive Brokers (Flex) | `ibkr_item.rb`, `provider/ibkr_flex.rb` | Global | **Keep** | IBKR serves Singapore residents through Interactive Brokers Singapore Pte. Ltd. The Flex Web Service is account-level and not region-gated ([IBKR Flex Web Service](https://www.interactivebrokers.com/campus/ibkr-api-page/flex-web-service/)). |
| SnapTrade | `snaptrade_item.rb` | Brokerage-dependent | **Keep** | Lists Interactive Brokers (read-only), and its access guide lists Moomoo, scoped to the US and Canada ([broker access guide](https://docs.snaptrade.com/docs/broker-access-guide), [Moomoo page](https://snaptrade.com/brokerage-integrations/moomoo-api)). No Tiger or other Singapore-local broker found. Its value in Singapore is mainly IBKR, which duplicates the direct IBKR provider. |
| Sharesight | `sharesight_item.rb` | Global | **Keep** | Supports SGX holdings and dividends ([Sharesight SGX](https://www.sharesight.com/blog/track-stocks-singapore-exchange-sharesight/)) and imports from Standard Chartered Singapore ([blog](https://www.sharesight.com/blog/automatically-import-trades-standard-chartered-singapore)). The code already maps `SGX => XSES` (`app/models/sharesight_account/data_helpers.rb`). |
| Wise | `wise_item.rb` | Global | **Keep** | Wise Asia-Pacific Pte. Ltd. is a MAS-licensed Major Payment Institution ([Wise regulation](https://wise.com/help/articles/2932693/how-wise-is-regulated)). Caveat: Wise's personal-token docs describe tokens for a *business* account and limit some endpoints ([personal API tokens](https://docs.wise.com/guides/developer/auth-and-security/personal-api-token)). Whether a Singapore personal account can pull statements needs a hands-on check. |
| Coinbase | `coinbase_item.rb` | Global (licensed in SG) | **Keep** | MAS granted Coinbase Singapore an MPI licence in October 2023 ([Coinbase/MAS](https://cointelegraph.com/news/coinbase-secures-payment-license-singapore), *(secondary)*). |
| Kraken | `kraken_item.rb` | Global | **Keep (flag)** | Secondary sources say Singapore residents can open accounts, but SGD isn't supported and a MAS licence application is still pending ([MoneySmart](https://www.moneysmart.sg/crypto/kraken) *(secondary)*). Check against [Kraken's regulation page](https://support.kraken.com/articles/where-is-kraken-licensed-or-regulated) before relying on it. |
| CoinStats | `coinstats_item.rb`, `provider/coinstats.rb` | Global aggregator | **Keep** | Region-agnostic portfolio aggregator over `openapiv1.coinstats.app`, and needs an API key. It covers wallets and exchanges, including Singapore-licensed ones. |
| On-chain wallets | `onchain_wallet_item.rb` | None | **Keep** | Public-address tracking with no region dependency ([docs/providers/onchain-wallets.md](../providers/onchain-wallets.md)). |
| Lunch Flow | `lunchflow_item.rb` | Multi-region | **Unclear** | The homepage claims UK, EU, US, Canada, Brazil, MENA and "Asia-Pacific" (30+ countries) over GoCardless, Akahu, SnapTrade, Finicity and MX. It names no Singapore bank ([lunchflow.app](https://www.lunchflow.app)). None of those aggregators is known to cover Singapore banks, so "Asia-Pacific" probably means AU/NZ. Confirm on Lunch Flow's coverage page. |
| Binance | `binance_item.rb` (binance.com API) | Global, excluding SG | **Unclear, leans remove** | After MAS put Binance.com on its Investor Alert List in 2021, Binance.com stopped fiat deposits and spot trading for Singapore users ([The Block](https://www.theblock.co/news/markets/2021-09-27-binance-singapore-restrict-offerings-main-platform-118730), [Cointelegraph](https://cointelegraph.com/news/binance-blocks-fiat-deposits-and-spot-crypto-trading-for-singapore-users) *(secondary)*). No later reversal was found. Legacy accounts could still be read through the API, but new Singapore users can't trade. Keep `BinancePublic` (market data) either way; see below. |
| Mercury | `mercury_item.rb` | US companies | **Unclear** | Mercury requires the *company* to be formed in the US or a US territory, though non-US founders may apply ([Mercury eligibility](https://support.mercury.com/hc/en-us/articles/28770467511060-Eligibility)). A Singapore resident can use it only through a US entity. Remove unless the owner has one. |
| Brex | `brex_item.rb` | US companies | **Unclear** | Like Mercury, a US business account that needs a US entity and EIN. Keep only if the owner runs one. |
| Plaid | `plaid_item.rb` | US, CA, UK, EU | **Remove** | Plaid's coverage is US, Canada, UK and the EU ([Plaid global coverage](https://plaid.com/global/)). The code has only `us` and `eu` regions (`provider/plaid_adapter.rb`). |
| TrueLayer | `truelayer_item.rb` | UK, EU | **Remove** | PSD2 open banking ([TrueLayer coverage](https://truelayer.com/coverage/)). |
| Enable Banking | `enable_banking_item.rb` | EEA, UK | **Remove** | PSD2 ASPSPs selected by European country code (`provider/enable_banking.rb#get_aspsps`) ([Enable Banking](https://enablebanking.com/open-banking-apis)). |
| SimpleFIN | `simplefin_item.rb` | US (CA partial) | **Remove** | US-focused bridge ([SimpleFIN Bridge](https://bridge.simplefin.org)). No Singapore institutions. |
| Sophtron | `sophtron_item.rb` | US, CA | **Remove** | Covers about 15,000 US and Canadian institutions ([Firefly III Sophtron docs](https://docs.firefly-iii.org/tutorials/data-importer/sophtron/), [review](https://fintechreview.net/sophtron-review-ai-driven-financial-data-access) *(secondary)*). |
| FinanceKit (Apple Wallet) | `financekit_item.rb` | US, UK | **Remove** | Apple lists US (Apple Card, Cash, Savings) and UK open banking only ([Apple FinanceKit](https://developer.apple.com/financekit/)). |
| Akahu | `akahu_item.rb` | New Zealand | **Remove** | NZ open-finance aggregator ([akahu.nz](https://www.akahu.nz)). |
| Up | `up_item.rb` | Australia | **Remove** | Australian neobank (`api.up.com.au`) ([Up API](https://developer.up.com.au)). |
| Redbark | `redbark_item.rb` | Australia | **Remove** | Australian CDR banks only ([docs/providers/redbark.md](../providers/redbark.md)). |
| CoinSpot | `coinspot_item.rb` | Australia | **Remove** | Australian exchange (`coinspot.com.au`), AUD-only ([coinspot.com.au](https://www.coinspot.com.au)). |
| Monobank | `monobank_item.rb` | Ukraine | **Remove** | Ukrainian bank ([api.monobank.ua](https://api.monobank.ua/docs/)). |
| Fio | `fio_item.rb` | Czech Republic | **Remove** | Czech bank API ([docs/providers/fio.md](../providers/fio.md)). |
| Indexa Capital | `indexa_capital_item.rb` | Spain | **Remove** | Spanish robo-advisor for Spanish residents ([indexacapital.com](https://indexacapital.com)). |
| Questrade | `questrade_item.rb` | Canada | **Remove** | Canadian broker for Canadian residents ([questrade.com](https://www.questrade.com)). |
| Trade Republic | `trade_republic_item.rb` | EU | **Remove** | Serves EEA countries only ([traderepublic.com](https://traderepublic.com)). |
| Trading 212 | `trading212_item.rb` | UK, EEA | **Remove** | No source confirms Singapore onboarding. Trading 212 says to check the country picker under "Open account" ([community](https://community.trading212.com/t/in-which-countries-t212-is-available-and-what-if-moved-abroad/6040)). Its entities serve the UK and EU. |

## Market data providers (`app/models/provider/`)

| Provider | Concept | Key? | Verdict | Evidence and notes |
|---|---|---|---|---|
| Yahoo Finance | Securities, FX | **Keyless** | **Keep** | Probed: `D05.SI` (DBS) returns SGD prices from exchange `SES`. Code gap: `map_exchange_mic` handles `SINGAPORE`/`SGX` for country, but no `SES` → `XSES` MIC mapping was found. Worth a follow-up. |
| Twelve Data | Securities, FX | Key (`TWELVE_DATA_API_KEY`) | **Keep** | Probed: `/exchanges?country=Singapore` returns `XSES`. Uses MIC codes directly, so SGX works. Free plan limits apply ([pricing](https://twelvedata.com/pricing)). |
| EODHD | Securities | Key (`EODHD_API_KEY`) | **Keep** | The vendor lists the Singapore exchange as code `SG` ([exchanges list](https://eodhd.com/financial-apis/list-supported-exchanges/)). Code gap: `MIC_TO_EODHD_EXCHANGE` has no `XSES => "SG"`, so SGX doesn't work today. |
| Alpha Vantage | Securities | Key (`ALPHA_VANTAGE_API_KEY`) | **Keep** | Global; useful for US-listed holdings. `MIC_TO_AV_SUFFIX` has no SGX entry ([docs](https://www.alphavantage.co/documentation/)). |
| Tiingo | Securities | Key (`TIINGO_API_KEY`) | **Keep** | Covers US and China only (`TIINGO_EXCHANGE_TO_MIC`), but still useful for US ETFs, which are common in Singapore portfolios ([tiingo.com](https://www.tiingo.com)). The weakest keep. |
| Frankfurter | FX | **Keyless** | **Keep** | Probed: `/v1/latest?base=SGD` returns rates ([frankfurter.dev](https://frankfurter.dev)). |
| Binance Public | Crypto prices | **Keyless** | **Keep** | Public market data endpoints, independent of account eligibility. Probed: `/api/v3/ticker/price` works ([Binance spot API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api)). |
| Blockscout | EVM chain explorer | **Keyless** | **Keep** | No region dependency ([docs/providers/onchain-wallets.md](../providers/onchain-wallets.md)). |
| Etherscan | EVM history | Optional key | **Keep** | Optional; only raises rate limits ([Etherscan v2](https://docs.etherscan.io/)). |
| mempool.space | Bitcoin explorer | **Keyless** | **Keep** | [mempool.space API](https://mempool.space/docs/api/rest) |
| Solana RPC | Solana | **Keyless** | **Keep** | Public RPC endpoint. |
| Jupiter tokens | SPL token metadata | **Keyless** | **Keep** | Public token list. |
| Polkadot Sidecar | Polkadot | **Keyless** | **Keep** | Parity's public instance. |
| Cosmos REST | Cosmos Hub | **Keyless** | **Keep** | Public LCD endpoint. |
| Mansa | African exchanges | Key | **Remove** | Covers African exchanges such as NGX and JSE (file header comment; [mansaapi.com](https://mansaapi.com)). |
| MFAPI | Indian mutual funds | **Keyless** | **Remove** | Probed: returns Indian AMFI schemes, for example SBI Small Cap ([mfapi.in](https://www.mfapi.in)). |
| MOEX | Russian securities, RUB FX | **Keyless** | **Remove** | Moscow Exchange ISS ([iss.moex.com](https://iss.moex.com/iss/reference/)). |
| T-Bank (Tinkoff) Invest | Russian instrument logos and prices | Key | **Remove** | Needs a T-Bank brokerage token ([T-Invest API](https://developer.tbank.ru/invest/intro/intro)). |
| RentCast | Property valuation | Key | **Remove** | US addresses only ([rentcast.io](https://www.rentcast.io/api)). |
| Realie | Property valuation | Key | **Remove** | US parcel data ([docs.realie.ai](https://docs.realie.ai)). |
| Chimnie | Property valuation | Key | **Remove** | UK, keyed by UPRN ([chimnie.co.uk](https://www.chimnie.co.uk)). |

Removing RentCast, Realie and Chimnie leaves **no property valuation provider**. See HDB and URA below.

## Unclear cases to settle by hand

1. **Lunch Flow**: check its coverage page for any Singapore bank. Likely there is none.
2. **Binance**: does the owner have a legacy Binance.com account? If not, remove the sync provider and keep `BinancePublic`.
3. **Mercury and Brex**: keep only if the owner operates a US entity.
4. **Kraken**: check against Kraken's own regulation page and the [MAS Financial Institutions Directory](https://eservices.mas.gov.sg/fid).
5. **Wise**: check whether a Singapore *personal* account token can read balances and statements.

## Singapore-relevant sources not supported (informational)

Not verified in depth. Starting points only.

- **[SGFinDex](https://www.mas.gov.sg/development/fintech/sgfindex)**: the MAS and GovTech consented data exchange for banks, insurers, CPF, HDB and IRAS, authenticated with Singpass. Only approved apps can join (for example Seedly and Planner Bee), so it's unlikely to be open to a self-hosted app.
- **MAS exchange rates and Singapore Government Securities data**: official SGD reference rates and SGS/T-bill/SSB yields through the [MAS API portal](https://eservices.mas.gov.sg/apimg-portal/).
- **[data.gov.sg](https://data.gov.sg) HDB resale prices**: keyless open data that could support a rough HDB valuation provider.
- **[URA Data Service](https://www.ura.gov.sg/maps/api/)**: private residential transaction data. Free, but needs registration and an access key.
- **[Tiger Brokers OpenAPI](https://quant.itigerup.com/openapi/en/python/overview/introduction.html)** and **[moomoo/Futu OpenAPI](https://openapi.moomoo.com/moomoo-api-doc/en/intro/intro.html)**: official APIs from two brokers popular in Singapore. SnapTrade's Moomoo integration is scoped to the US and Canada.
- **[Saxo OpenAPI](https://www.developer.saxo/)**: Saxo Markets has a Singapore entity.
- **Singapore-licensed crypto exchanges** (for example Coinhako, Gemini, OKX SG, Crypto.com and Independent Reserve SG): check MAS licence status in the FID before adding any. Some are reachable today through CoinStats.
- **CPF, CDP (SGX depository), Endowus, Syfe, StashAway**: no public personal-data APIs found. Statement import (CSV or PDF) is the realistic path.
