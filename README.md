# Razvoj mikroservisne web-aplikacije za upravljanje poslovnim angažmanima i digitalnim ugovorima – poslužiteljski sloj

**Sveučilište:** [Sveučilište Jurja Dobrile u Puli](https://www.unipu.hr/)<br>
**Fakultet:** [Fakultet informatike u Puli](https://fipu.unipu.hr/)<br>
**Studentica:** Roberta Starčić<br>
**JMBAG:** 0351011388<br>
**Studijski smjer:** Informatika<br>
**Kolegij:** Raspodijeljeni sustavi<br>
**Znanstveno područje:** Društvene znanosti<br>
**Znanstveno polje:** Informacijske znanosti<br>
**Znanstvena grana:** Informacijski sustavi i informatologija<br>
**Mentor:** izv. prof. dr. sc. Nikola Tanković<br>
**Mjesto i datum:** Pula, rujan 2026.

Ovaj repozitorij sadržava izvorni kod poslužiteljskog sloja sustava **WorkLink**, razvijenog kao praktični dio diplomskog rada pod naslovom *Razvoj mikroservisne web-aplikacije za upravljanje poslovnim angažmanima i digitalnim ugovorima*.

## Sažetak

Najveći izazov digitalnog posredovanja nije pronaći poslovnog partnera, nego sigurno i dosljedno upravljati svime što slijedi nakon njihova povezivanja. Objavljivanje oglasa i podnošenje prijave tek su početak procesa koji obuhvaća pregovaranje, prihvaćanje uvjeta, sklapanje ugovora, praćenje izvršenja, plaćanje i izgradnju povjerenja između korisnika.

Ovaj rad odgovara na rascjepkanost takva procesa razvojem sustava **WorkLink**, čiji je cilj navedene aktivnosti povezati u jedinstven tijek vođen jasno određenim poslovnim pravilima. Razvoju sustava prethodila je analiza platformi Upwork, Fiverr i Freelancer.com, na temelju koje su utvrđene ključne faze životnog ciklusa poslovnog angažmana i oblikovani zahtjevi sustava.

WorkLink je implementiran primjenom mikroservisnog pristupa te povezuje korisničku aplikaciju razvijenu bibliotekom React s četirima mikroservisima zaduženima za autentifikaciju, poslovne procese, ugovore i plaćanja. Razvijeni prototip obuhvaća cjelokupan tijek angažmana – od objave posla i podnošenja prijave do generiranja i potpisivanja ugovora, izvršenja posla, testnog plaćanja putem sustava Stripe i ocjenjivanja korisnika.

Implementacija pokazuje da se povezani poslovni postupci mogu objediniti primjenom mikroservisnog pristupa uz jasno razdvojene odgovornosti pojedinih servisa.

**Ključne riječi:** mikroservisna arhitektura, poslovni angažman, digitalni ugovor, web-aplikacija
