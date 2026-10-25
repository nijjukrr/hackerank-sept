from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path("code").resolve()))
from intent_classifier import IntentClassifier

class SyntheticIntentClassificationTest(unittest.TestCase):
    """Synthetic adversarial test cases for intent classification."""

    def test_affirmative_multilingual_deletions(self):
        cases = [
            ("English", "Please delete my account and all associated data permanently."),
            ("English", "I want to erase all my personal information."),
            ("English", "Kindly close and purge my customer profile."),
            ("Spanish", "Por favor elimine mi cuenta permanentemente."),
            ("Spanish", "Solicito borrar todos mis datos personales."),
            ("French", "Veuillez supprimer mon compte et effacer mes données."),
            ("French", "Demande de clôture définitive de mon profil."),
            ("German", "Bitte löschen Sie mein Kundenkonto und entfernen Sie meine Daten."),
            ("German", "Schließen Sie bitte mein Konto endgültig."),
            ("Portuguese", "Por favor apagar minha conta e excluir meus registros."),
            ("Italian", "Desidero cancellare il mio account e rimuovere i miei dati."),
            ("Japanese", "私のアカウントと個人情報を完全に削除してください。"),
            ("Korean", "내 계정을 영구적으로 삭제하고 개인정보를 지워주세요."),
        ]
        for lang, text in cases:
            self.assertTrue(
                IntentClassifier.authorizes_deletion(text),
                f"Failed to identify affirmative deletion intent for {lang}: '{text}'"
            )

    def test_adversarial_non_deletion_negations(self):
        cases = [
            ("Do not delete", "I am having login issues. Do not delete my account."),
            ("Don't erase", "Please send my receipts, don't erase anything."),
            ("Not asking for deletion", "I want an export of my transactions. I am not asking for deletion."),
            ("Information request", "Can you provide a summary of my data? This is an information request, not a request to delete."),
            ("Marketing only", "Please unsubscribe me from marketing lists only, leave the account active."),
            ("Still use account", "Fix my name spelling on the invoice. I still use the account."),
            ("Keep profile", "I need to change my credit card. Please keep my profile active."),
            ("Continue service", "Update my delivery address. I want to continue using the service."),
            ("Without removing", "Can you fix the order error without removing my account?"),
        ]
        for name, text in cases:
            self.assertFalse(
                IntentClassifier.authorizes_deletion(text),
                f"Adversarial non-deletion false-positive on '{name}': '{text}'"
            )

if __name__ == "__main__":
    unittest.main()
