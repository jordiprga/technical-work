"""Local research dashboard: ``streamlit run app.py``.

The UI only displays recorded, held-out experiments or explicitly trains one.
It never substitutes illustrative numbers for experiment results.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
SOURCES = ["bernoulli", "markov", "higher_order", "periodic", "hmm", "ar1", "arcsine", "drift", "long_range", "nonlinear"]
MODELS = ["marginal", "markov1", "markov2", "markov3", "markov4", "markov5", "ppm", "lz78", "gb", "rf", "mlp", "gru", "transformer", "flow"]
COLORS = ["#57e1da", "#a890ff", "#f9b66e", "#74b9ff", "#f48fb1", "#a7dd82"]

st.set_page_config(page_title="Entropy Oracle", page_icon="◈", layout="wide")
st.markdown(
    """<style>
    .stApp {background: #0a111c; color: #e7edf6;}
    [data-testid="stSidebar"] {background: #101b2b;}
    .block-container {padding-top: 2.4rem; max-width: 1510px;}
    h1 {letter-spacing: -.045em; font-weight: 750 !important;}
    h2,h3 {letter-spacing: -.02em;}
    .eyebrow {color: #57e1da; font: 600 .73rem monospace; letter-spacing:.19em;}
    .subtitle {color: #a4b3c8; max-width: 850px; line-height: 1.6;}
    .status {display: inline-block; border: 1px solid #29435c; color: #b5c9dc;
             padding: .25rem .6rem; border-radius: 20px; font-size: .72rem;}
    [data-testid="stMetric"] {border: 1px solid #253449; border-radius: 12px;
                             padding: 1rem; background: #101a29;}
    [data-testid="stMetricLabel"] {color: #a4b3c8;}
    .stButton>button[kind="primary"] {background:#57e1da; color:#07121b; border:0; font-weight:700;}
    </style>""",
    unsafe_allow_html=True,
)


def themed(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#101a29", font=dict(family="sans-serif", color="#cbd7e6"),
        margin=dict(l=16, r=16, t=32, b=24), colorway=COLORS,
        legend=dict(orientation="h", y=-.2),
    )
    fig.update_xaxes(gridcolor="#26344a")
    fig.update_yaxes(gridcolor="#26344a")
    return fig


def probability_trace(result: dict, model: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract a trace defensively; old saved schemas can lack trace data."""
    trace = result.get("trace", {})
    y = np.asarray(trace.get("y", []), dtype=int)
    probs = np.asarray(trace.get("probabilities", {}).get(model, []), dtype=float)
    indices = np.asarray(trace.get("indices", list(range(len(y)))))
    if probs.ndim != 2:
        return np.array([]), np.array([], dtype=int), np.empty((0, 0))
    n = min(len(y), len(probs), len(indices))
    return indices[:n], y[:n], probs[:n]


def learning_curve_records(directory: Path) -> list[dict]:
    """Read actual fixed-test learning experiments; never invent missing points."""
    records = []
    for path in sorted(directory.glob("*.json")):
        try:
            run = json.loads(path.read_text())
            config = run.get("config", {})
            train_size = config.get("train_size")
            if train_size is None:
                continue
            for row in run.get("metrics", []):
                records.append(dict(row, train_size=int(train_size), source=config.get("source", "unknown"), seed=config.get("seed", 0), artifact=path.name))
        except (OSError, ValueError, AttributeError, TypeError):
            continue
    return records


@st.cache_data(ttl=5, show_spinner=False)
def saved_experiment_files(directory: str) -> list[Path]:
    """Discover nested experiment artifacts, excluding summary/contrast JSON."""
    root = Path(directory)
    files = []
    for path in root.rglob("*.json"):
        try:
            result = json.loads(path.read_text())
            if isinstance(result, dict) and isinstance(result.get("config"), dict) and isinstance(result.get("metrics"), list):
                files.append(path)
        except (OSError, ValueError):
            continue
    def priority(path: Path) -> tuple[int, str]:
        relative = str(path.relative_to(root))
        if relative == "v2/main/nonlinear_seed211_n12000.json":
            return 0, relative
        if relative == "main/nonlinear_seed11_n12000.json":
            return 1, relative
        return 2, relative
    return sorted(files, key=priority)


def install_result(result: dict, path: Path | None = None) -> None:
    """Replace the active experiment and discard any previous download payload."""
    st.session_state["oracle_result"] = result
    st.session_state["oracle_result_path"] = str(path) if path is not None else None
    st.session_state.pop("oracle_npz_bytes", None)
    st.session_state.pop("oracle_npz_metadata", None)


def render_result(result: dict) -> None:
    rows = result.get("metrics", [])
    if not rows:
        st.info("Este archivo no contiene una tabla de métricas reconocida.")
        st.json(result)
        return
    frame = pd.DataFrame(rows)
    if "model" not in frame:
        st.error("La tabla de resultados debe identificar cada predictor con 'model'.")
        return
    config = result.get("config", {})
    source_metadata = result.get("source_metadata", {})
    if result.get("schema_version", 1) < 2:
        st.warning("Resultado histórico · esquema v1. Conserva las arquitecturas y el protocolo originales, incluido el MLP anterior. Usa los experimentos results/v2 para comparar la implementación actual.")
    selection = result.get("selection", {})
    selected = selection.get("selected_model", "—")
    selected_row = frame.loc[frame.model == selected]
    # Explicit backend selection, never choose the highest test score in this UI.
    accuracy = float(selected_row.iloc[0]["accuracy"]) if len(selected_row) else None
    oracle = frame.loc[frame.model == "oracle"]
    cols = st.columns(4)
    cols[0].metric("Fuente", config.get("source", "—"))
    cols[1].metric("Seleccionado en validación", str(selected))
    cols[2].metric("Acierto test · seleccionado", f"{accuracy:.2%}" if accuracy is not None else "—")
    cols[3].metric("Referencia óptima · acierto test", f"{float(oracle.iloc[0]['accuracy']):.2%}" if len(oracle) else "No disponible")
    st.caption(
        "La selección y los pesos se fijan usando validación. Las gráficas siguientes describen el test temporal final. "
        "Un predictor entrenado no certifica una cota inferior de min-entropía de la fuente."
    )
    if len(oracle) and "oracle_expected_accuracy" in oracle:
        st.caption(f"Referencia teórica condicionada al pasado observado: promedio de max P = {float(oracle.iloc[0]['oracle_expected_accuracy']):.4f}. El acierto realizado puede diferir por variabilidad muestral.")
    bootstrap_available = any(row.get("bootstrap_ci_low") is not None for row in rows)
    if source_metadata.get("stationary") is False:
        st.info("Fuente no estacionaria: el bootstrap estacionario por bloques no está justificado. Usa los intervalos martingala para el promedio de éxito condicional del tramo evaluado.")
    elif not bootstrap_available:
        st.caption("Bootstrap por bloques excluido o desactivado en esta ejecución. Los intervalos de éxito mostrados son los del protocolo martingala registrado.")
    bootstrap_policy = result.get("bootstrap_policy", {})
    if bootstrap_policy.get("requested", 0) > 0 and bootstrap_policy.get("effective") == 0:
        st.caption(f"Bootstrap excluido por el protocolo: {bootstrap_policy.get('reason', 'no se han establecido los supuestos de estacionariedad y mezcla')}.")
    comparison_tab, traces_tab, training_tab, audit_tab = st.tabs(
        ["Comparación", "Predicciones y errores", "Entrenamiento", "Método y reproducibilidad"]
    )

    with comparison_tab:
        left, right = st.columns(2)
        plot_data = frame.dropna(subset=["accuracy"]).copy()
        if {"success_ci_low", "success_ci_high"}.issubset(plot_data):
            plot_data["error_plus"] = (plot_data.success_ci_high - plot_data.accuracy).clip(lower=0)
            plot_data["error_minus"] = (plot_data.accuracy - plot_data.success_ci_low).clip(lower=0)
            error_args = dict(error_y="error_plus", error_y_minus="error_minus")
        else:
            error_args = {}
        with left:
            st.subheader("Probabilidad de acierto")
            fig = px.bar(plot_data, x="model", y="accuracy", color="model", **error_args,
                         color_discrete_sequence=COLORS)
            fig.update_layout(showlegend=False)
            fig.update_yaxes(range=[0, 1], tickformat=".0%", title="Fracción de aciertos fuera de muestra")
            fig.update_xaxes(title=None)
            st.plotly_chart(themed(fig), use_container_width=True)
        with right:
            st.subheader("Log-loss predictivo")
            if "log_loss_bits" in frame:
                fig = px.bar(frame, x="model", y="log_loss_bits", color="model", color_discrete_sequence=COLORS)
                fig.update_layout(showlegend=False)
                fig.update_yaxes(title="Bits / muestra · menor es mejor")
                fig.update_xaxes(title=None)
                st.plotly_chart(themed(fig), use_container_width=True)
        st.caption("Las barras de incertidumbre corresponden a los intervalos de éxito registrados en el experimento; consulta su estimando y supuestos en Método. Log-loss y min-entropía son magnitudes distintas.")
        st.subheader("Métricas y coste computacional")
        preferred = ["model", "accuracy", "val_accuracy", "log_loss_bits", "success_ci_low", "success_ci_high", "guess_probability_model", "fit_seconds", "predict_seconds", "process_peak_rss_mb"]
        visible = [c for c in preferred if c in frame]
        st.dataframe(frame[visible], hide_index=True, use_container_width=True)
        st.caption("Memoria: pico RSS del proceso completo durante ajuste/predicción; incluye bibliotecas y memoria reutilizada de otros modelos. No representa memoria aislada por arquitectura.")
        st.download_button("Descargar métricas CSV", frame.to_csv(index=False), "entropy-oracle-metrics.csv", "text/csv")
        marginal = result.get("empirical_marginal")
        if marginal:
            with st.expander("Distribución marginal observada"):
                fig = px.bar(x=list(range(len(marginal))), y=marginal, labels={"x": "Símbolo", "y": "Frecuencia empírica"}, color_discrete_sequence=[COLORS[0]])
                fig.add_hline(y=1 / len(marginal), line_dash="dot", line_color=COLORS[1], annotation_text="Uniforme")
                st.plotly_chart(themed(fig, 280), use_container_width=True)
                st.caption("Una marginal uniforme no implica independencia temporal. Frecuencias empíricas calculadas sobre la secuencia completa para descripción, sin utilizarlas para ajustar predictores.")
        comparisons = result.get("comparisons", [])
        if comparisons:
            st.subheader("Comparaciones pareadas")
            st.dataframe(pd.DataFrame(comparisons), hide_index=True, use_container_width=True)
        if selection.get("ensemble_weights"):
            weights = pd.DataFrame(list(selection["ensemble_weights"].items()), columns=["model", "weight"])
            st.subheader("Pesos del ensemble fijados en validación")
            st.dataframe(weights, hide_index=True, use_container_width=True)

    with traces_tab:
        available = list(result.get("trace", {}).get("probabilities", {}))
        if not available:
            st.info("Este resultado no incluye una traza de probabilidades.")
        else:
            choice = st.selectbox("Predictor que explorar", available, key="trace_model")
            t, y, p = probability_trace(result, choice)
            if not len(y):
                st.info("No hay muestras de test en esta traza.")
            else:
                limit = st.slider("Muestras visibles", min_value=1, max_value=len(y), value=min(200, len(y)), key="trace_limit") if len(y) > 1 else 1
                symbol = st.selectbox("Símbolo cuya probabilidad mostrar", list(range(p.shape[1])), key="trace_symbol")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=t[:limit], y=p[:limit, symbol], name=f"q(X={symbol} | pasado)", line=dict(color=COLORS[0])))
                fig.add_trace(go.Scatter(x=t[:limit], y=(y[:limit] == symbol).astype(int), mode="markers", name=f"Observado X={symbol}", marker=dict(size=5, color=COLORS[1], opacity=.55)))
                fig.update_yaxes(range=[-.04, 1.04], title="Probabilidad / indicador")
                fig.update_xaxes(title="Índice temporal en la secuencia")
                st.plotly_chart(themed(fig, 360), use_container_width=True)
                predicted = p.argmax(axis=1)
                a, b = st.columns(2)
                with a:
                    st.subheader("Confusión · traza guardada")
                    confusion = np.zeros((p.shape[1], p.shape[1]), dtype=int)
                    np.add.at(confusion, (y, predicted), 1)
                    fig = go.Figure(go.Heatmap(z=confusion, x=list(range(p.shape[1])), y=list(range(p.shape[1])), colorscale="Teal", hovertemplate="Real %{y}<br>Predicho %{x}<br>N=%{z}<extra></extra>"))
                    fig.update_xaxes(title="Símbolo predicho")
                    fig.update_yaxes(title="Símbolo real")
                    st.plotly_chart(themed(fig, 320), use_container_width=True)
                with b:
                    st.subheader("Errores individuales")
                    errors = pd.DataFrame({"índice": t, "real": y, "predicho": predicted, "q(real)": p[np.arange(len(y)), y], "confianza": p.max(axis=1)})
                    st.dataframe(errors.loc[y != predicted].head(100), hide_index=True, use_container_width=True)
                st.caption(f"Diagnóstico de {len(y):,} muestras guardadas. La tabla de métricas utiliza el test completo.")

    with training_tab:
        histories = result.get("histories", {})
        records = [dict(record, model=name) for name, history in histories.items() for record in (history or [])]
        if records:
            hist = pd.DataFrame(records)
            if "epoch" not in hist:
                hist["epoch"] = hist.groupby("model").cumcount() + 1
            losses = [c for c in ["train_loss", "val_loss"] if c in hist]
            if losses:
                long = hist.melt(id_vars=["epoch", "model"], value_vars=losses, var_name="partición", value_name="loss").dropna(subset=["loss"])
                fig = px.line(long, x="epoch", y="loss", color="model", line_dash="partición", color_discrete_sequence=COLORS)
                fig.update_yaxes(title="Pérdida · bits / símbolo")
                st.plotly_chart(themed(fig, 430), use_container_width=True)
                st.caption("El checkpoint puede seleccionarse por pérdida de validación. Esta curva no constituye una evaluación independiente.")
                if "mlp" in hist.model.values:
                    st.caption("MLP: la pérdida de entrenamiento incluye la penalización L2 de scikit-learn, convertida junto con la log-loss de nats a bits. Por ello no es log-loss predictiva pura. La tabla de test sí informa log-loss predictiva sin penalización.")
            st.dataframe(hist, hide_index=True, use_container_width=True)
        else:
            st.info("Los predictores de este experimento no registraron curvas por época.")
        learning = learning_curve_records(ROOT / "results" / "v2" / "learning") or learning_curve_records(ROOT / "results" / "learning")
        if learning:
            st.subheader("Curvas de aprendizaje · tamaño del conjunto de entrenamiento")
            learning_frame = pd.DataFrame(learning)
            groups = list(learning_frame[["source", "seed"]].drop_duplicates().itertuples(index=False, name=None))
            group = st.selectbox("Fuente / semilla de la curva", groups, format_func=lambda pair: f"{pair[0]} · semilla {pair[1]}")
            curve = learning_frame.loc[(learning_frame.source == group[0]) & (learning_frame.seed == group[1])].sort_values("train_size")
            curve_a, curve_b = st.columns(2)
            with curve_a:
                fig = px.line(curve, x="train_size", y="accuracy", color="model", markers=True, color_discrete_sequence=COLORS)
                fig.update_xaxes(title="Muestras de entrenamiento")
                fig.update_yaxes(title="Acierto en test", tickformat=".0%")
                st.plotly_chart(themed(fig, 380), use_container_width=True)
            with curve_b:
                fig = px.line(curve, x="train_size", y="log_loss_bits", color="model", markers=True, color_discrete_sequence=COLORS)
                fig.update_xaxes(title="Muestras de entrenamiento")
                fig.update_yaxes(title="Log-loss · bits / muestra")
                st.plotly_chart(themed(fig, 380), use_container_width=True)
            st.caption("Cada punto procede de un artefacto de aprendizaje guardado; se usa results/v2/learning cuando está disponible. Las curvas son análisis exploratorios: comparar repetidamente sobre un test compartido no crea nuevas validaciones independientes.")
            with st.expander("Mediciones de las curvas"):
                st.dataframe(curve, hide_index=True, use_container_width=True)

    with audit_tab:
        st.markdown("**Qué estima cada métrica**")
        st.markdown(
            "La precisión mide el éxito observado de la regla de decisión `argmax q`. "
            "El promedio de `max q` es una confianza del modelo y no la probabilidad real de acierto. "
            "La log-loss es el promedio de `−log₂ q(Xₜ | pasado)`. No equivale a min-entropía."
        )
        st.latex(r"P_{\rm guess}=\mathbb{E}_{H}\max_x P(X=x\mid H),\qquad \widetilde H_\infty(X\mid H)=-\log_2 P_{\rm guess}")
        st.markdown(
            "Un predictor subóptimo proporciona evidencia de predictibilidad: una cota inferior válida de su éxito "
            "puede dar una **cota superior** de la average conditional min-entropy, con el mismo estimando. "
            "No proporciona por sí solo una cota inferior conservadora de entropía. "
            "Los intervalos martingala se refieren al promedio de probabilidades condicionales en el tramo evaluado; "
            "no garantizan el comportamiento de una fuente futura bajo drift. "
            "El bootstrap por bloques requiere hipótesis adicionales de estacionariedad y mezcla."
        )
        st.caption("Prototipo de investigación. La relación con los predictores de SP 800-90B es experimental; no es una implementación normativa de SP 800-90B ni AIS 31.")
        st.markdown("**Configuración reproducible**")
        st.json(config)
        st.markdown("**Referencia y metadatos de la fuente**")
        st.json(source_metadata)
        limitations = result.get("limitations", [])
        source_limitations = [str(value) for key, value in source_metadata.items() if "limitation" in key.lower()]
        if limitations or source_limitations:
            st.markdown("**Limitaciones declaradas de esta ejecución**")
            for limitation in source_limitations + limitations:
                st.markdown(f"- {limitation}")
        other = {k: v for k, v in result.items() if not k.startswith("_") and k not in {"config", "source_metadata", "metrics", "trace", "histories", "comparisons"}}
        with st.expander("Detalles del protocolo y selección"):
            st.json(other)
    public_result = {key: value for key, value in result.items() if not key.startswith("_")}
    if "_audit" in result:
        if st.button("Preparar archivo NPZ completo"):
            from entropy_oracle.artifacts import write_prediction_archive
            with tempfile.TemporaryDirectory(prefix="entropy-oracle-download-") as directory:
                destination = Path(directory) / "entropy-oracle-result.predictions.npz"
                metadata = write_prediction_archive(result["_audit"], destination)
                st.session_state["oracle_npz_bytes"] = destination.read_bytes()
                st.session_state["oracle_npz_metadata"] = metadata
        if "oracle_npz_bytes" in st.session_state:
            public_result["prediction_archive"] = st.session_state["oracle_npz_metadata"]
            st.download_button("Descargar predicciones completas NPZ", st.session_state["oracle_npz_bytes"], "entropy-oracle-result.predictions.npz", "application/octet-stream")
    elif st.session_state.get("oracle_result_path"):
        archive = Path(st.session_state["oracle_result_path"]).with_suffix(".predictions.npz")
        if archive.is_file():
            st.download_button("Descargar predicciones completas NPZ", archive.read_bytes(), archive.name, "application/octet-stream")
    st.download_button("Descargar resultado JSON", json.dumps(public_result, indent=2, ensure_ascii=False), "entropy-oracle-result.json", "application/json")


st.markdown('<div class="eyebrow">ADVERSARIAL PREDICTION LAB</div>', unsafe_allow_html=True)
st.title("Entropy Oracle")
st.markdown('<p class="subtitle">Explora lo que revela el pasado. Compara predictores sobre fuentes controladas o capturas reales y mide su éxito en un test temporal independiente.</p>', unsafe_allow_html=True)
st.markdown('<span class="status">LOCAL · REPRODUCIBLE · OUT-OF-SAMPLE</span>', unsafe_allow_html=True)
st.write("")

with st.sidebar:
    st.header("Laboratorio")
    st.caption("Elige una fuente, fija la semilla y ejecuta el mismo protocolo para todos los modelos.")
    source_mode = st.radio("Origen de los datos", ["Fuente sintética", "Archivo local"], key="source_mode")
    uploaded_file = None
    input_alphabet = 256
    input_dtype = "uint8"
    if source_mode == "Fuente sintética":
        source = st.selectbox("Fuente de datos", SOURCES, index=SOURCES.index("nonlinear"))
        n = int(st.number_input("Número de muestras", min_value=500, max_value=1_000_000, value=12000, step=1000))
    else:
        source, n = "file", 0
        uploaded_file = st.file_uploader("Secuencia discreta", type=["bin", "npy", "csv", "txt"], key="input_file")
        input_alphabet = int(st.number_input("Tamaño del alfabeto", min_value=2, max_value=256, value=256, step=1, help="Número de símbolos posibles. Cada muestra debe ser un entero entre 0 y A−1; no se recodifica automáticamente."))
        input_dtype = st.selectbox("Codificación binaria (.bin)", ["uint8", "uint16le", "uint32le"], help="Enteros sin signo; uint16le y uint32le usan little-endian. CSV/TXT/NPY conservan sus valores enteros.")
        st.caption("El archivo se procesa en memoria en este servidor local y no se envía a servicios externos. La aplicación no guarda automáticamente el archivo ni los resultados.")
        st.caption("Se utiliza la secuencia completa en el orden del archivo. CSV/TXT: una única columna de enteros, sin cabecera. NPY: vector de enteros, sin objetos Python.")
    seed = int(st.number_input("Semilla", min_value=0, max_value=2**31 - 1, value=0, step=1))
    window = int(st.slider("Ventana de pasado", min_value=5, max_value=128, value=32))
    selected_models = st.multiselect("Predictores", MODELS, default=["marginal", "markov5", "ppm", "mlp", "gru", "transformer", "flow"])
    with st.expander("Parámetros avanzados"):
        epochs = int(st.number_input("Épocas de redes", min_value=1, max_value=200, value=15))
        bootstrap = int(st.number_input("Réplicas bootstrap", min_value=0, max_value=10000, value=400, step=100))
        raw_params = st.text_area("Parámetros de la fuente (JSON)", value="{}", height=100, help='Ejemplo Bernoulli: {"p": 0.8}. Los nombres se validan en el generador.') if source_mode == "Fuente sintética" else "{}"
    train = st.button("Entrenar y evaluar", type="primary", use_container_width=True)
    st.caption("Separación temporal train / validation / test. El entrenamiento se ejecuta en el proceso local.")
    st.divider()
    st.subheader("Resultados guardados")
    files = saved_experiment_files(str(ROOT / "results"))
    if files:
        selected_file = st.selectbox("Experimento", files, format_func=lambda p: str(p.relative_to(ROOT / "results")))
        if st.button("Abrir resultado", use_container_width=True):
            try:
                loaded = json.loads(selected_file.read_text())
                if isinstance(loaded, dict) and isinstance(loaded.get("metrics"), list):
                    install_result(loaded, selected_file)
                else:
                    st.warning("Este archivo es un resumen o curva; abre un resultado individual de experimento.")
            except (OSError, ValueError) as exc:
                st.error(f"No se pudo leer el resultado: {exc}")
    else:
        st.caption("Ejecuta benchmark.py para guardar experimentos en results/.")

if train:
    try:
        params = json.loads(raw_params)
        if not isinstance(params, dict):
            raise ValueError("Los parámetros deben ser un objeto JSON.")
        if not selected_models:
            raise ValueError("Selecciona al menos un predictor.")
        input_data = None
        if source_mode == "Archivo local":
            if uploaded_file is None:
                raise ValueError("Selecciona un archivo local antes de entrenar.")
            from entropy_oracle.data import load_discrete_bytes
            input_data = load_discrete_bytes(uploaded_file.getvalue(), uploaded_file.name, alphabet_size=input_alphabet, dtype=input_dtype)
            n = len(input_data.x)
        from entropy_oracle.experiment import run_experiment
        with st.status("Preparando entrenamiento temporal…", expanded=True) as training_status:
            def progress(message: str) -> None:
                training_status.update(label=str(message).split(": test accuracy=")[0])
                training_status.write(message)
            arguments = dict(source=source, n=n, seed=seed, models=selected_models, window=window, epochs=epochs, source_params=params, bootstrap=bootstrap, progress=progress)
            if input_data is not None:
                arguments["data"] = input_data
            result = run_experiment(**arguments)
            training_status.update(label="Entrenamiento y evaluación completados", state="complete", expanded=False)
        install_result(result)
        st.success("Experimento terminado. Las métricas proceden de la ejecución real.")
    except ValueError as exc:
        st.error(f"No se pudo completar el experimento: {exc}")
    except Exception as exc:
        st.error(f"No se pudo completar el experimento: {type(exc).__name__}: {exc}")
        with st.expander("Detalles técnicos"):
            st.exception(exc)

if "oracle_result" in st.session_state:
    render_result(st.session_state["oracle_result"])
else:
    st.info("Configura el laboratorio y pulsa Entrenar y evaluar, o abre un experimento ya guardado.")
    a, b, c = st.columns(3)
    a.markdown("**01 · Fuentes y capturas**\n\nGeneradores con referencias conocidas, o secuencias discretas propias en BIN, NPY, CSV y TXT. Conserva el orden temporal de cada captura.")
    b.markdown("**02 · Búsqueda adversarial**\n\nFrecuencias, contextos, árboles, redes y flujos condicionales compiten sobre la misma secuencia.")
    c.markdown("**03 · Evidencia medible**\n\nAcierto, log-loss, incertidumbre, errores y coste de entrenamiento. Ningún número se genera antes de ejecutar.")
