# Multi-Chain Blockchain Sistem

Ovaj **multi-chain blockchain sistem** ima sledeće komponente:

## 1. Master Chain  
Centralni entitet koji vodi evidenciju o svim sidechain-ovima i njihovim čvorovima.  
- Registrovanje novih sidechain-ova  
- Čuvanje metapodataka (endpoint adrese, status)  
- Orkestracija zahteva između korisnika i sidechain-ova  

## 2. Sidechain-ovi  
Individualni blockchain-ovi sa svojom SQLite bazom.  
- Svaki sidechain može imati **više čvorova (node-ova)**  
- Perzistentno skladišti podatke specifične za taj lanac  
- Sinhronizuje podatke između čvorova  

## 3. Čvorovi (Node-ovi)  
Instance svakog sidechain-a koje rade na različitim portovima.  
- Svaki čvor može prihvatati transakcije i sinhronizovati ih sa drugim čvorovima u istom sidechain-u  
- Povezan sa SQLite bazom koja čuva njegovu lokalnu kopiju blockchain-a  

---

## **Struktura dijagrama**
1. **Master Chain na vrhu**  
   - Prikazan kao centralna komponenta  
   - Povezan sa više sidechain-ova  

2. **Sidechain-ovi u sredini**  
   - Svaki sidechain ima svoju SQLite bazu  
   - Više čvorova unutar svakog sidechain-a  

3. **Čvorovi (node-ovi) na dnu**  
   - Svaki node prikazan kao pojedinačna instanca koja sinhronizuje blokove  

---

## **Priprema okruženja**
Na svim hostovima instalirati:

```sh
sudo apt install -y python3.12-venv
python3 -m venv myenv
source myenv/bin/activate
pip install apscheduler flask requests
```

Iskopirati na sve hostove:
```
masterchain.py
blockchain.py
sidechain.py
```

---

## **Pokretanje aplikacije**
### Na master čvoru:
```sh
python masterchain.py
```

### Na nodovima (hostovima):
**Prvi nod:**  
```sh
python sidechain.py sidechain1 5001
```
(*ime mreže i port čvora formiraju jedinstveno ime baze: `imemreze-port.db`*)

**Drugi nod:**  
```sh
python sidechain.py sidechain1 5001
```

**Treći nod:**  
```sh
python sidechain.py sidechain2 5001
python sidechain.py sidechain1 5002
python sidechain.py sidechain1 5003
```

---

## **Registrovanje sidechain-ova**
```sh
curl -X POST http://192.168.122.11:4000/register_sidechain      -H "Content-Type: application/json"      -d '{"name": "Sidechain-1", "node_url": "http://192.168.122.12:5001"}'

curl -X POST http://192.168.122.11:4000/register_sidechain      -H "Content-Type: application/json"      -d '{"name": "Sidechain-1", "node_url": "http://192.168.122.13:5001"}'

curl -X POST http://192.168.122.11:4000/register_sidechain      -H "Content-Type: application/json"      -d '{"name": "Sidechain-2", "node_url": "http://192.168.122.14:5001"}'
```

---

## **Registrovanje nodova u sidechain mreži**
```sh
./register_nodes.sh Sidechain-1
```
(*Za `Sidechain-1` generiše P2P mrežu nodova pozivom:*)  
```sh
curl -X GET http://192.168.122.11:4000/get_sidechains
```
(*a prethodno je mreža registrovana na novom nodu/portu pozivom:*)  
```sh
curl -X POST http://192.168.122.11:4000/register_sidechain
```

---

## **Dodavanje bloka u sidechain**
```sh
curl -X POST http://192.168.122.12:5001/mine      -H "Content-Type: application/json"      -d '{"data": "Test block"}'
```

## **Čitanje blokova iz sidechain-a sa noda**
```sh
curl -X GET http://192.168.122.12:5001/blocks
```

## **Čitanje sidechain-ova sa master-a**
```sh
curl -X GET http://192.168.122.11:4000/get_sidechains
```

## **Sinhronizacija sidechain-ova i blokova sa master-a**
```sh
curl -X GET http://192.168.122.11:4000/sync_sidechains
```
