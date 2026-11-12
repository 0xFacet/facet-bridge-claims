# Facet bridge claims

The Facet bridges closed on 2026‑11‑12 at Ethereum block 26,401,162 (Facet block 5,055,804). Balances at that block decide everything here.

- **Bridged ETH (WETH on Facet)** was sent directly to holders in 47 batches from the WETH bridge `0x0000000000000b07ED001607f5263D85bf28Ce4C`: 256.255414 ETH to 9,272 addresses. The list is in `eth/payout.csv`. Nothing to claim.
- **Bridged Ethscriptions** (eths, Facet, gwei, dumb, mfpurrs, nodes) are claimed from each token's original L1 bridge contract. Each bridge stores a Merkle root of who receives which inscriptions. This repository holds the data needed to claim.

| Token | Bridge (claim here) | claimRoot | Recipients | Inscriptions |
|---|---|---|---:|---:|
| eths | `0x03f84C2b50442332802b7ca8DBbEfAd1633F2547` | `0xdd66ab8f6d25c8f8657da7449496afe60297ff21fa780df9ca9d0ed094abee00` | 915 | 8,996 |
| Facet | `0x061eAf68B2069Ed7708af1893f4499960a0156c5` | `0x202291497aca00247979ed35a0b08dedf2579a036c424b581cc7305e9960a084` | 494 | 8,409 |
| gwei | `0x91DC93cD8336d30a4679b1d29C9592C117a896FD` | `0x52a7e359ab656c68f9207bc0f619da08b015c2f896b7c1719169af675a151811` | 55 | 924 |
| dumb | `0xB01278c0FC86D1CD4DE513ca03BF7dACc2DBD1A4` | `0x62b93dd6c3534a4c874bc8286000be97bc524098019ebaf4af01de82f2921321` | 114 | 1,802 |
| mfpurrs | `0xAFd1c394F054eF0845e64429AAAF8c6CA8F51306` | `0x06f1bac696df13d8fa337d288a7abf0f6f587d01419834de76f2cf7b90a4ab67` | 56 | 2,358 |
| nodes | `0x000000000006F291B587f39B6960dd32e31400bF` | `0x8f74cfd0ee1545519be01cd224f597e05464d329f7a636c4ddc6a17c83555ab4` | 533 | 629,083 |

## Find your claim

Open `claims/<token>/<your address in lowercase>.json`. No file means no whole inscription of that token for that address (holdings are rounded to whole inscriptions by a largest-remainder rule). A file has one or more leaves of up to 500 inscriptions; each leaf is one claim transaction.

## Claim

Anyone may submit a claim; the inscriptions always go to the recipient written in the leaf. The sender pays gas. Claims do not expire.

**Etherscan:** open the token's bridge address → Contract → Write as Proxy → Connect wallet → `claim`, and enter from your file: `leafIndex`, `recipient`, `ids` (the whole array) and `proof` (the whole array). Repeat for each leaf. `isClaimed(leafIndex)` under Read as Proxy shows whether a leaf has been claimed.

**cast:**

```bash
cast send <bridge> "claim(uint256,address,bytes32[],bytes32[])" <leafIndex> <recipient> '[0x...,0x...]' '[0x...,0x...]' --rpc-url <rpc> <your signer flags>
```

## Verify

`python3 verify.py claims/<token>/<address>.json` checks your proofs against the file's root; `python3 verify.py --all` checks every package and file (Python 3, nothing to install). Compare the root with the bridge's `settlement()` → `claimRoot` on Etherscan (Read as Proxy). Any copy of these files, from anywhere, is valid if its root matches the one on chain.

## How this was computed

The snapshot, attribution rules, rounding and the run log are in [github.com/0xFacet/facet-bridge-api](https://github.com/0xFacet/facet-bridge-api) under `shutdown/` (data in `shutdown/data/live-2026-11-12/`). The claim contract is `FacetEthscriptionBridgeV7` (`0x5dDF2BdC128D1940A5a7F385f6D2Eb744ba828BE`, verified on Sourcify), installed on each bridge proxy with these roots. The bridges' upgrade admin (the Facet multisig) is retained, as the shutdown plan describes.
