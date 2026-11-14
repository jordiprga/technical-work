# Borrador para revisión humana — no enviado

Destino posible: ICMC 2027, charla de 30 minutos, track Certification Programs o Random Bit Generators. El organizador exige propuestas neutrales respecto a proveedores; comprobar información actual antes de cualquier uso.

**Title:** From Passing Tests to Reviewable Evidence: Reproducible Assurance for Entropy Sources

**Draft abstract:**

Cryptographic validation depends on more than a passing test result. Reviewers need to know which product configuration was tested, which assumptions support the claim, and whether the evidence remains applicable after a change. This talk presents a practical, vendor-neutral workflow for keeping those relationships explicit.

Using public standards references and synthetic entropy-source examples, we separate four questions: whether artifact bytes are intact, whether a procedure can be replayed, whether its assumptions are justified, and who is authorized to accept the resulting evidence. An offline prototype illustrates content-addressed evidence, externally pinned manifests, deterministic check replay, and conservative change-impact reporting. The examples deliberately include evidence that passes a technical check but still requires expert review.

The session also uses feedback and extractor-seed examples to show why an apparently healthy output distribution cannot replace a stated source model and adversary assumptions. Attendees receive a minimal evidence-package design and a review checklist that can be implemented alongside existing validation tooling. The workflow supports preparation and review; it does not issue certificates, establish source entropy from statistics alone, or replace accredited evaluation.

## Antes de enviar

Jordi debe verificar personalmente que la demo sigue reproduciéndose, revisar las referencias normativas y decidir autoría, afiliación y disponibilidad. Los ejemplos de feedback/extracción deben presentarse con hipótesis completas. No incluir métricas de ahorro ni validación comercial: aún no se han medido. Declarar uso de IA conforme a las reglas aplicables y conservar procedencia. No se ha creado cuenta, contactado al comité ni enviado esta propuesta.

Fuente del plazo observado: [convocatoria oficial](https://icmconference.org/speaking/), consultada 14 noviembre 2026; cierre anunciado 16 noviembre 2026.
