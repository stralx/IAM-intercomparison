import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FormatStrFormatter
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches
import re
import math

def iam_intercomparison_figure(hist_df, AR6_df, study_df,
                               scenarios=None,
                               region_list=['EU28','EU27'],
                               box_cats=['C1','C2','C3']):
    """
        Create a grid of scenario plots with:
          - Historical dashed line (sum over region_list in hist_df)
          - Model lines per scenario (study_df filtered on region_list)
          - Min–max funnel & median from 2020 (study_df)
          - Boxplots at 2050 (AR6_df filtered on region_list, variable, box_cats)
          - Legends for models and box categories in bottom‑right panel

        Parameters:
          hist_df : DataFrame with columns ['model','scenario','region','variable','year','value']
          AR6_df  : DataFrame with columns ['model','scenario','region','Category','variable','year','value']
          study_df : DataFrame with columns ['model','scenario','region','variable','year','value']
          scenarios : list of scenario strings
          region_list : tuple of two regions to sum for hist and filter for spag/box
          box_cats : tuple of three category strings for boxplots
        """
    # --- 1) Metadata ---
    study_name = study_df['study'].iat[0].replace("_", " ")
    var = study_df['variable'].iat[0]
    region_label = re.sub(r'^EU.*', 'EU', region_list[0])
    unit = study_df['unit'].iat[0]

    # --- 2) Boxplot data at 2050 ---
    cats = list(box_cats)

    bx = AR6_df
    data2050 = [bx[bx['Category'] == c]['value'].values for c in cats]

    n = len(scenarios)
    is_even = (n % 2 == 0)

    # --- 4) Colors ---
    models = sorted(study_df['model'].unique())
    palette = plt.rcParams['axes.prop_cycle'].by_key()['color']
    model_colors = {m: palette[i % len(palette)] for i, m in enumerate(models)}
    box_colors = {cats[0]: '#ffcccc', cats[1]: '#ff6666', cats[2]: '#cc0000'}

    # --- 5) Grid layout (+ extra cell for odd) ---
    total_panels = n + (0 if is_even else 1)
    ncols = int(math.ceil(math.sqrt(total_panels)))
    nrows = int(math.ceil(total_panels / ncols))
    fig, axes = plt.subplots(
        nrows, ncols,
        figsize=(5 * ncols, 4 * nrows),
        sharey=True,
        gridspec_kw={'wspace': 0.05, 'hspace': 0.3}
    )
    axes = axes.flatten()

    # --- 6) Plot each scenario ---
    for idx, scen in enumerate(scenarios):
        ax = axes[idx]

        # historical
        ax.plot(hist_df['year'], hist_df['value'], '--k', lw=2)

        # models
        df_s = study_df[study_df['scenario'] == scen]
        for model, grp in df_s.groupby('model', observed=True):
            ax.plot(grp['year'], grp['value'], color=model_colors[model], alpha=0.7, lw=1.5)

        # funnel
        post = df_s[df_s['year'] >= 2020]
        if not post.empty:
            pv = post.groupby('year', observed=True, as_index=False)['value'].agg(min_value='min', max_value='max')
            ax.fill_between(pv['year'], pv['min_value'], pv['max_value'], color='lightgray', alpha=0.3)
            # med = post.groupby('year', observed=True, as_index=False)['value'].median()   # uncomment for median
            # ax.plot(med['year'], med['value'], color='gray', lw=2)                        # uncomment for median

        # boxplots
        box_x = [2052, 2054, 2056]
        bp = ax.boxplot(data2050, positions=box_x, widths=1.3, patch_artist=True, showfliers=False)
        for i, cat in enumerate(cats):
            b = bp['boxes'][i]
            b.set_facecolor(box_colors[cat]); b.set_edgecolor('black'); b.set_alpha(0.8)

        ymin, ymax = ax.get_ylim()
        # ax.axvline(2015, color='gray', linestyle=':', lw=1.5)                                 #uncomment for WILIAM vline
        # ax.text(2015, ymax * 0.60, 'WILLIAM\n Base year\n2015', ha='right', va='top', color='gray', fontsize=6)  #uncomment for WILIAM vline
        ax.axvline(2020, color='gray', linestyle=':', lw=1.5)
        ax.text(2020, ymax * 0.60, 'Base year 2020', ha='right', va='top', fontsize=6, color='gray')
        ax.set_title(scen, fontsize=9); ax.grid(axis='y', linestyle='--', alpha=0.5)
        ax.xaxis.set_major_locator(FixedLocator(range(1990, 2060, 10)))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%d'))
        ax.tick_params(axis='x', rotation=45, labelsize=8); ax.tick_params(axis='y', labelsize=8)
        ax.set_xlim(2000, 2060)
        ylabel = f"{unit}"

    # --- 7) Hide unused axes ---
    for j in range(n + (0 if is_even else 1), len(axes)):
        axes[j].axis('off')

    # --- 8) Legend handles ---
    region0 = hist_df['region'].iat[0]
    model_handles = [Line2D([0],[0], color='black', linestyle='--', linewidth=2, label=f'Historical ({region0})')]
    model_handles += [Line2D([0],[0], color=model_colors[m], linewidth=3, label=f"{m} ({study_df.loc[study_df['model']==m,'region'].iat[0]})") for m in models]
    box_handles = [mpatches.Patch(facecolor=box_colors[c], edgecolor='black', label=f'AR6 SSP2-{c}') for c in cats]

    # --- 9) Place legends ---
    if is_even:
        mleg = fig.legend(handles=model_handles, loc="center left", bbox_to_anchor=(0.83,0.6), title=study_name, frameon=False)
        mleg.get_title().set_fontweight('bold')
        blem = fig.legend(handles=box_handles, loc="center left", bbox_to_anchor=(0.83,0.35), title=f'AR6 2050 projections ({region_label})', frameon=False)
        blem.get_title().set_fontweight('bold')
        fig.subplots_adjust(right=0.75)
    else:
        legend_ax = axes[n]; legend_ax.axis('off')
        mleg = legend_ax.legend(handles=model_handles, loc="upper center", ncol=1, title=study_name, frameon=False)
        mleg.get_title().set_fontweight('bold'); legend_ax.add_artist(mleg)
        blem = legend_ax.legend(handles=box_handles, loc="lower center", ncol=1, title=f'AR6 2050 projections ({region_label})', frameon=False)
        blem.get_title().set_fontweight('bold'); legend_ax.add_artist(blem)

    # --- 10) Title & layout ---
    fig.suptitle(f"{study_name} – {var} \nRegion: {region_label}",
                 x=0.5, y=1.02, ha="center", fontsize=12, fontweight="bold")

    fig.supylabel(ylabel, fontsize=12)

    plt.tight_layout(rect=[0,0,1,0.95]);
    plt.show()
