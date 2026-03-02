"""
Voting Management System on a Simple Blockchain
================================================
Menu-driven console app with blockchain-backed vote recording.
"""

import hashlib
import json
from datetime import datetime


# ─────────────────────────────────────────────
#  Data Entities
# ─────────────────────────────────────────────

class Voter:
    def __init__(self, voter_id: str, name: str):
        self.voter_id  = voter_id
        self.name      = name
        self.has_voted = False

    def __repr__(self):
        status = "voted" if self.has_voted else "not voted"
        return f"Voter({self.voter_id}, {self.name}, {status})"


class Candidate:
    def __init__(self, candidate_id: str, name: str):
        self.candidate_id = candidate_id
        self.name         = name

    def __repr__(self):
        return f"Candidate({self.candidate_id}, {self.name})"


# ─────────────────────────────────────────────
#  Blockchain
# ─────────────────────────────────────────────

class Block:
    def __init__(self, index: int, transactions: list, previous_hash: str):
        self.index         = index
        self.timestamp     = datetime.utcnow().isoformat()
        self.transactions  = transactions
        self.previous_hash = previous_hash
        self.hash          = self._compute_hash()

    def _compute_hash(self) -> str:
        block_data = json.dumps({
            "index":         self.index,
            "timestamp":     self.timestamp,
            "transactions":  self.transactions,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def __repr__(self):
        tx_str = json.dumps(self.transactions, indent=4)
        return (
            f"\n{'='*62}\n"
            f"  Block #{self.index}\n"
            f"  Timestamp    : {self.timestamp}\n"
            f"  Transactions :\n{tx_str}\n"
            f"  Prev Hash    : {self.previous_hash}\n"
            f"  Hash         : {self.hash}\n"
            f"{'='*62}"
        )


class Blockchain:
    def __init__(self):
        self.chain = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis = Block(0, [{"type": "genesis", "message": "Genesis Block"}], "0" * 64)
        self.chain.append(genesis)

    @property
    def latest_block(self) -> "Block":
        return self.chain[-1]

    def add_block(self, transactions: list) -> "Block":
        block = Block(len(self.chain), transactions, self.latest_block.hash)
        self.chain.append(block)
        return block

    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current  = self.chain[i]
            previous = self.chain[i - 1]
            # Recompute and compare
            if current.hash != current._compute_hash():
                return False
            # Verify linkage
            if current.previous_hash != previous.hash:
                return False
        return True

    def print_chain(self):
        print("\n" + "=" * 62)
        print("       B L O C K C H A I N   L E D G E R")
        print("=" * 62)
        for block in self.chain:
            print(block)


# ─────────────────────────────────────────────
#  Voting System
# ─────────────────────────────────────────────

class VotingSystem:
    def __init__(self):
        self.blockchain = Blockchain()
        self.voters:     dict[str, Voter]     = {}
        self.candidates: dict[str, Candidate] = {}

    # ── menu ──────────────────────────────────────────────────────

    def _print_menu(self):
        print("\n" + "-" * 42)
        print("   BLOCKCHAIN VOTING MANAGEMENT SYSTEM")
        print("-" * 42)
        print("  1. Add Candidate")
        print("  2. Add Voter")
        print("  3. Cast Vote")
        print("  4. Print Blockchain")
        print("  5. Validate Chain")
        print("  6. Exit")
        print("-" * 42)

    # ── action handlers ───────────────────────────────────────────

    def add_candidate(self):
        cid = input("Enter candidate ID  : ").strip()
        if not cid:
            print("[!] Candidate ID cannot be empty.")
            return
        if cid in self.candidates:
            print(f"[!] Candidate ID '{cid}' already exists.")
            return
        name = input("Enter candidate name: ").strip()
        if not name:
            print("[!] Name cannot be empty.")
            return
        self.candidates[cid] = Candidate(cid, name)
        print(f"[OK] Candidate '{name}' (ID: {cid}) added.")

    def add_voter(self):
        vid = input("Enter voter ID  : ").strip()
        if not vid:
            print("[!] Voter ID cannot be empty.")
            return
        if vid in self.voters:
            print(f"[!] Voter ID '{vid}' already exists.")
            return
        name = input("Enter voter name: ").strip()
        if not name:
            print("[!] Name cannot be empty.")
            return
        self.voters[vid] = Voter(vid, name)
        print(f"[OK] Voter '{name}' (ID: {vid}) registered.")

    def cast_vote(self):
        if not self.voters:
            print("[!] No voters registered yet.")
            return
        if not self.candidates:
            print("[!] No candidates available yet.")
            return

        print("\nAvailable Candidates:")
        for c in self.candidates.values():
            print(f"  [{c.candidate_id}] {c.name}")

        vid = input("\nEnter your voter ID           : ").strip()
        if vid not in self.voters:
            print(f"[!] Voter ID '{vid}' not found.")
            return
        voter = self.voters[vid]
        if voter.has_voted:
            print(f"[!] '{voter.name}' has already voted. Double-voting is not allowed.")
            return

        cid = input("Enter candidate ID to vote for: ").strip()
        if cid not in self.candidates:
            print(f"[!] Candidate ID '{cid}' not found.")
            return
        candidate = self.candidates[cid]

        transaction = {
            "type"        : "vote",
            "voter_id"    : voter.voter_id,
            "voter_name"  : voter.name,
            "candidate_id": candidate.candidate_id,
            "candidate"   : candidate.name,
            "timestamp"   : datetime.utcnow().isoformat(),
        }
        block = self.blockchain.add_block([transaction])
        voter.has_voted = True

        print(f"\n[OK] Vote recorded!  '{voter.name}'  ->  '{candidate.name}'")
        print(f"     Block #{block.index}  |  Hash: {block.hash[:24]}...")

    def print_blockchain(self):
        self.blockchain.print_chain()

        # Live tally from chain data
        tally = {cid: 0 for cid in self.candidates}
        for block in self.blockchain.chain[1:]:          # skip genesis
            for tx in block.transactions:
                if tx.get("type") == "vote" and tx["candidate_id"] in tally:
                    tally[tx["candidate_id"]] += 1

        if tally:
            print("\n  CURRENT VOTE TALLY")
            print("  " + "-" * 32)
            for cid, count in tally.items():
                print(f"  {self.candidates[cid].name:<22} : {count} vote(s)")
        print()

    def validate_chain(self):
        if self.blockchain.is_valid():
            print("[OK] Blockchain is VALID — no tampering detected.")
        else:
            print("[!!] Blockchain is INVALID — data may have been tampered with!")

    # ── main loop ─────────────────────────────────────────────────

    def run(self):
        print("\nWelcome to the Blockchain Voting Management System!")
        while True:
            self._print_menu()
            choice = input("Enter your choice (1-6): ").strip()

            if   choice == "1": self.add_candidate()
            elif choice == "2": self.add_voter()
            elif choice == "3": self.cast_vote()
            elif choice == "4": self.print_blockchain()
            elif choice == "5": self.validate_chain()
            elif choice == "6":
                print("\nExiting... Goodbye!\n")
                break
            else:
                print("[!] Invalid choice. Please enter a number between 1 and 6.")


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    VotingSystem().run()