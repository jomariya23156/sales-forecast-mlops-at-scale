import pandas as pd
import matplotlib.pyplot as plt


def plot_store_data(df: pd.DataFrame) -> None:
    plt.rcParams.update({"font.size": 22})
    fig, ax = plt.subplots(figsize=(20, 10))
    df.plot(x="ds", y="y", ax=ax)
    ax.set_xlabel("Date")
    ax.set_ylabel("Sales")
    ax.legend(["Truth"])
    current_ytick_values = plt.gca().get_yticks()
    plt.gca().set_yticklabels(["{:,.0f}".format(x) for x in current_ytick_values])
    plt.savefig("store_data.png")


def plot_forecast(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    predicted: pd.DataFrame,
    train_index: int,
) -> None:
    fig, ax = plt.subplots(figsize=(20, 10))
    df_test.plot(
        x="ds",
        y="y",
        ax=ax,
        label="Truth",
        linewidth=1,
        markersize=5,
        color="tab:blue",
        alpha=0.9,
        marker="o",
    )
    predicted.plot(
        x="ds",
        y="yhat",
        ax=ax,
        label="Prediction + 95% CI",
        linewidth=2,
        markersize=5,
        color="red",
    )
    ax.fill_between(
        x=predicted["ds"],
        y1=predicted["yhat_upper"],
        y2=predicted["yhat_lower"],
        alpha=0.15,
        color="red",
    )
    df_train.iloc[train_index - 100 :].plot(
        x="ds",
        y="y",
        ax=ax,
        color="tab:blue",
        label="_nolegend_",
        alpha=0.5,
        marker="o",
    )
    current_ytick_values = plt.gca().get_yticks()
    plt.gca().set_yticklabels(["{:,.0f}".format(x) for x in current_ytick_values])
    ax.set_xlabel("Date")
    ax.set_ylabel("Sales")
    plt.tight_layout()
    plt.savefig("store_data_forecast.png")
