from app.services.pii_mask import mask_pii


def test_mask_pii_email_phone_cpf():
    text = "Contato: joao.silva@email.com telefone (11) 91234-5678 cpf 123.456.789-10"
    masked = mask_pii(text)

    assert "joao.silva@email.com" not in masked
    assert "91234-5678" not in masked
    assert "123.456.789-10" not in masked
    assert "[EMAIL]" in masked
    assert "[TELEFONE]" in masked
    assert "[CPF]" in masked
