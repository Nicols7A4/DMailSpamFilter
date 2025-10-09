from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from db.models import db, User, Message
from spamfilter.features import extract_features
from spamfilter.bn_model import infer_bn
from flask import current_app as app
import json

bp = Blueprint("web", __name__)

@bp.route("/inbox")
@login_required
def inbox():
    msgs_normal = Message.query.filter_by(recipient_id=current_user.id, is_spam=False)\
                               .order_by(Message.created_at.desc()).all()
    msgs_spam = Message.query.filter_by(recipient_id=current_user.id, is_spam=True)\
                             .order_by(Message.created_at.desc()).all()
    return render_template("inbox.html", msgs_normal=msgs_normal, msgs_spam=msgs_spam)

@bp.route("/compose", methods=["GET"])
@login_required
def compose():
    return render_template("compose.html")

@bp.route("/message/<int:msg_id>")
@login_required
def message_detail(msg_id):
    m = Message.query.get_or_404(msg_id)
    if m.recipient_id != current_user.id and m.sender_id != current_user.id:
        abort(403)
    if m.status == "unread" and m.recipient_id == current_user.id:
        m.status = "read"; db.session.commit()
    return render_template("message.html", m=m)

@bp.route("/api/message/<int:msg_id>/explanation")
@login_required
def message_explanation(msg_id):
    m = Message.query.get_or_404(msg_id)
    if m.recipient_id != current_user.id and m.sender_id != current_user.id:
        abort(403)
    try:
        data = json.loads(m.explanation) if m.explanation else {}
    except Exception:
        data = {"error": "explanation not available"}
    return jsonify(data)

@bp.route("/api/send", methods=["POST"])
@login_required
def api_send():
    data = request.get_json() or request.form
    to_email = (data.get("to") or "").strip().lower()
    subject = data.get("subject") or "(sin asunto)"
    body = data.get("body") or ""
    recipient = User.query.filter_by(email=to_email).first()
    if not recipient:
        return jsonify({"ok": False, "error": "Destinatario no existe"}), 400

    feats = extract_features(sender_email=current_user.email, recipient_id=recipient.id,
                             subject=subject, body=body)
    result = infer_bn(feats)
    is_spam = result["label"] == "spam"
    score = float(result["score"])
    report = {"features": feats, "rationale": result["rationale"], "score": score}

    msg = Message(
        sender_id=current_user.id, recipient_id=recipient.id,
        subject=subject, body=body,
        is_spam=is_spam, spam_score=score,
        explanation=json.dumps(report, ensure_ascii=False)
    )
    db.session.add(msg); db.session.commit()
    return jsonify({"ok": True, "message_id": msg.id})
