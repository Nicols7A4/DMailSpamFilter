from db.models import Whitelist

SPAM_WORDS = {"gratis","oferta","premio","urgente","haz clic","bono","lotería"}

def is_in_whitelist(recipient_id: int, sender_email: str) -> bool:
    return Whitelist.query.filter_by(user_id=recipient_id, trusted_email=sender_email).first() is not None

def extract_features(sender_email, recipient_id, subject, body):
    text = f"{subject} {body}".lower()
    hit_words = [w for w in SPAM_WORDS if w in text]
    links_count = text.count("http://") + text.count("https://")
    feats = {
        "SenderKnown": int(is_in_whitelist(recipient_id, sender_email)),
        "Keywords": int(len(hit_words) > 0),
        "Links": int(links_count > 0),
        "LengthShort": int(len(text.split()) < 30),
        "_meta": {"links_count": links_count, "hit_words": hit_words}
    }
    return feats
