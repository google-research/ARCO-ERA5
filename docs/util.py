import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import metview as mv
import numpy as np
from cartopy.mpl import ticker
from matplotlib import colors
from mpl_toolkits.axes_grid1 import axes_divider


__author__ = 'carver@google.com'


def plot_map(
        lats, 
        lons,
        x, 
        label,
        ax, 
        cmap,
        norm,
        coastlines=False,
        lakes=False,
        rivers=False,
        countries=False,
        states=False,
        counties=False,
        provinces=False,
    ):
    """Plot a map with data using Matplotlib and Cartopy.

    Args:
        lats (numpy.ndarray): Array of latitude values.
        lons (numpy.ndarray): Array of longitude values.
        x (numpy.ndarray): Data values to be plotted.
        label (str): Title for the plot.
        ax (matplotlib.axes.Axes): Matplotlib axes object to draw the map on.
        cmap (matplotlib.colors.Colormap): Colormap for coloring the data.
        norm (matplotlib.colors.Normalize): Normalize object for data scaling.
        coastlines (bool): Whether to plot coastlines.
        lakes (bool): Whether to plot lakes.
        rivers (bool): Whether to plot rivers.
        countries (bool): Whether to plot country borders.
        states (bool): Whether to plot state borders.
        counties (bool): Whether to plot county borders.
        provinces (bool): Whether to plot province borders.

    Returns:
        matplotlib.collections.QuadMesh: The QuadMesh object representing the plot.
    """

    if counties:
        counties_features = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_2_counties_lakes',
            scale='10m',
            edgecolor='gray',
            facecolor='none')
        ax.add_feature(counties_features)

    if states:
        ax.add_feature(cfeature.STATES, edgecolor='darkgray')
    if provinces:
        provinces_features = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='10m',
            facecolor='none')
        ax.add_feature(provinces_features, edgecolor='gray')
    if countries:
        ax.add_feature(cfeature.BORDERS, edgecolor='black')
    if rivers:
        ax.add_feature(cfeature.RIVERS, edgecolor='blue')
    if lakes:
        ax.add_feature(cfeature.LAKES, edgecolor='black', facecolor='none')
    if coastlines:
        ax.add_feature(cfeature.COASTLINE, edgecolor='black')

    lon_we = (lons + 180) % 360 - 180

    ax.set_extent([lon_we.min(), np.ceil(lon_we.max()), lats.min(), np.ceil(lats.max())], crs=ccrs.PlateCarree())
    ax.set_xticks(np.linspace(lon_we.min(), np.ceil(lon_we.max()), 7), crs=ccrs.PlateCarree())
    ax.set_yticks(np.linspace(lats.min(), np.ceil(lats.max()), 7), crs=ccrs.PlateCarree())

    lon_formatter = ticker.LongitudeFormatter(zero_direction_label=True, degree_symbol="", number_format=".1f")
    lat_formatter = ticker.LatitudeFormatter(degree_symbol="", number_format=".1f")
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)

    p = ax.pcolormesh(lons, lats, x,
                      transform=ccrs.PlateCarree(),
                      cmap=cmap,
                      norm=norm)

    ax.set_title(label)
    ax.set_xlabel('')
    ax.set_ylabel('')
    return p


def plot_barbs(lats, lons, u, v, ax, skip=4):
    """Plot wind barbs on a map.

    Args:
        lats (numpy.ndarray): Array of latitude values.
        lons (numpy.ndarray): Array of longitude values.
        u (numpy.ndarray): U-component of wind data.
        v (numpy.ndarray): V-component of wind data.
        ax (matplotlib.axes.Axes): Matplotlib axes object to draw the map on.
        skip (int): Skip factor for plotting wind barbs (default is 4).

    Returns:
        matplotlib.quiver.Quiver: Quiver object representing the wind barbs.
    """
    p = ax.barbs(
        lons[::skip], lats[::skip], u[::skip, ::skip], v[::skip, ::skip],
        color='k',
        transform=ccrs.PlateCarree(),
    )
    return p


def plot_shaded_with_barbs(plot_ds,
                           shading_variable='si10',
                           label="Wind Speed (m/s)",
                           cmap='viridis',
                           plot_wind_barbs=True,
                           barb_skip=4,
                           scalevar=1.0, add_offset=0.0,
                           coastlines=True,
                           lakes=False,
                           rivers=False,
                           countries=False,
                           states=False,
                           counties=False,
                           provinces=False,
                           uvar="u10",
                           vvar="v10",
                           figsize=(12, 15)):
    """Plot shaded data on a map with optional wind barbs.

    Args:
        plot_ds (xarray.Dataset): Dataset containing the data to be plotted.
        shading_variable (str): Name of the variable to be used for shading.
        label (str): Label for the plot.
        cmap (str or matplotlib.colors.Colormap): Colormap for coloring the data.
        plot_wind_barbs (bool): Whether to plot wind barbs (default is True).
        barb_skip (int): Skip factor for plotting wind barbs (default is 4).
        scalevar (float): Scaling factor for the shading variable (default is 1.0).
        add_offset (float): Offset to be added to the shading variable (default is 0.0).
        coastlines (bool): Whether to plot coastlines (default is True).
        lakes (bool): Whether to plot lakes (default is False).
        rivers (bool): Whether to plot rivers (default is False).
        countries (bool): Whether to plot country borders (default is False).
        states (bool): Whether to plot state borders (default is False).
        counties (bool): Whether to plot county borders (default is False).
        provinces (bool): Whether to plot province borders (default is False).
        uvar (str): Name of the U-component of wind variable (default is "u10").
        vvar (str): Name of the V-component of wind variable (default is "v10").
        figsize (tuple): Figure size (width, height) (default is (12, 15)).

    Returns:
        None
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(2, 1, 1, projection=ccrs.PlateCarree())
    ax.set_global()
    divider = axes_divider.make_axes_locatable(ax)

    min_bound = plot_ds[shading_variable].min() * scalevar + add_offset
    max_bound = plot_ds[shading_variable].max() * scalevar + add_offset
    norm = colors.Normalize(min_bound, max_bound)

    im = plot_map(plot_ds.latitude, plot_ds.longitude,
                  (plot_ds[shading_variable] * scalevar + add_offset),
                  label, ax, cmap=cmap, norm=norm,
                  coastlines=coastlines,
                  lakes=lakes,
                  rivers=rivers,
                  countries=countries,
                  states=states,
                  provinces=provinces,
                  counties=counties,
                  )

    if plot_wind_barbs:
        sp = plot_barbs(plot_ds.latitude, plot_ds.longitude,
                        plot_ds[uvar].values, plot_ds[vvar].values,
                        ax, skip=barb_skip)
    cax = divider.append_axes("right", size="2%", pad=0.05,
                              axes_class=plt.Axes)
    fig.colorbar(im, cax=cax)


def shaded_plot(fieldset, **kwargs):
    """Create a shaded plot with optional wind vectors and customizations.

    Args:
        fieldset (xarray.Dataset): Dataset containing the data to be plotted.
        **kwargs: Keyword arguments for customizing the plot.

    Keyword Args:
        shortName (str): The shortName of the field to plot (default is "ws").
        plotWind (bool): True to overlay wind vectors (default is False).
        level (int): The level to plot (default is 137).
        line (list): Line with coordinates [Lat1, Lon1, Lat2, Lon2] (default is [0, 0, 0, 0]).
        plotLine (bool): True to plot the line (default is False).
        scaleFactor (float): Rescale the variable by scaleFactor (default is 1.0).
        scaleBias (float): Adjust the rescaled variable by a constant factor (default is 0.0).
        styleName (str): Contour style to use (default is "sh_all_f03t70_beauf").
        coastLatSpacing (int): Spacing of latitude labels in degrees (default is 15).
        coastLonSpacing (int): Spacing of longitude labels in degrees (default is 20).
        mapAdministrativeBoundaries (str): "on" to plot administrative boundaries (default is "off").
        mapAdministrativeBoundariesColour (str): Administrative boundary color (default is "automatic").
        mapAdministrativeBoundariesCountriesList (list): List of countries to plot administrative boundaries
                                                        using ISO 3166-1 alpha-3 codes (default is []).
        mapAdministrativeBoundariesStyle (str): Administrative (states/provinces) boundary style (default is "dash").
        mapAdministrativeBoundariesThickness (int): Administrative boundary thickness (default is 1).
        mapAreaName (str): Plot a predefined region, overrides mapCorners (default is "").
        mapBoundaries (str): National boundaries (default is "on").
        mapBoundariesColour (str): National boundary color (default is "automatic").
        mapBoundariesThickness (int): National boundary thickness (default is 1).
        mapCoastLandShade (str): "on" to shade the land (default is "off").
        mapCoastSeaShade (str): "on" to shade the ocean (default is "off").
        mapCoastLineThickness (int): Coastline thickness (default is 1).
        mapCities (str): "on" to plot the capitals of each country (default is "off").
        mapCitiesFontSize (float): Font size for city labels (default is 2.5).
        mapCitiesMarkerHeight (float): Marker height for city labels (default is 0.7).
        mapCorners (list): Lat1, Lon1, Lat2, Lon2 of a plotting region (default is [-90, -180, 90, 180]).
        mapGrid (str): "on" to plot lat/lon grid lines (default is "off").
        mapLabelHeight (float): Font size for map labels (default is 0.4).
        mapRivers (str): "on" to plot major rivers (default is "off").
        outputWidth (int): Width of the output plot (default is 1800).
        textFontSize (float): Font size for text elements (default is 1.0).
        unitString (str): Custom unit string for the plot (default is "").
        windDensity (float): Wind density for wind vectors (default is 2.5).
        windFieldType (str): Type of wind vectors ("flags", "arrows", "streamlines") (default is "arrows").

    Returns:
        None
    """
    # The shortName of the field we want to plot
    shortName = kwargs.get("shortName", "ws")
    # True to overlay the vector winds
    plotWind = kwargs.get("plotWind", False)
    level = kwargs.get("level", 137)  # The level to plot
    # Line with coordinates [Lat1, Lon1, Lat2, Lon2]
    line = kwargs.get("line", [0, 0, 0, 0])
    plotLine = kwargs.get("plotLine", False)  # True to plot the line
    # Rescale the variable by scaleFactor
    scaleFactor = kwargs.get("scaleFactor", 1.0)
    # Adjust the rescaled variable by a constant factor
    scaleBias = kwargs.get("scaleBias", 0.0)
    # Contour style to use
    styleName = kwargs.get("styleName", "sh_all_f03t70_beauf")

    # Spacing Latitude labels in degrees
    coastLatSpacing = kwargs.get("coastLatSpacing", 15)
    # Spacing of longitude labels in degrees
    coastLonSpacing = kwargs.get("coastLonSpacing", 20)

    mapAdministrativeBoundaries = kwargs.get(
        "mapAdministrativeBoundaries", "off")  # "On" to plot states/provinces boundaries
    mapAdministrativeBoundariesColour = kwargs.get(
        "mapAdministrativeBoundariesColour", "automatic")  # Administrative boundary color
    mapAdministrativeBoundariesCountriesList = kwargs.get(
        "mapAdministrativeBoundariesCountriesList",
        [])  # List of countries to plot administrative boundaries using ISO 3166-1 alpha-3 codes
    mapAdministrativeBoundariesStyle = kwargs.get(
        "mapAdministrativeBoundariesStyle", "dash")  # Administrative (states/provinces) boundary style
    mapAdministrativeBoundariesThickness = kwargs.get(
        "mapAdministrativeBoundariesThickness", 1)  # Administrative boundary thickness

    mapAreaName = kwargs.get("mapAreaName", "")  # Plot a predefined region, overrides mapCorners

    mapBoundaries = kwargs.get("mapBoundaries", "on")  # National boundaries
    mapBoundariesColour = kwargs.get("mapBoundariesColour", "automatic")  # National boundary color
    mapBoundariesThickness = kwargs.get("mapBoundariesThickness", 1)
    mapCoastLandShade = kwargs.get("mapCoastLandShade", "off")  # On to shade the land
    mapCoastSeaShade = kwargs.get("mapCoastSeaShade", "off")  # On to shade the ocean
    mapCoastLineThickness = kwargs.get("mapCoastLineThickness", 1)
    mapCities = kwargs.get("mapCities", "off")  # On to plot the capitals of each country
    mapCitiesFontSize = kwargs.get("mapCitiesFontSize", 2.5)
    mapCitiesMarkerHeight = kwargs.get("mapCitiesMarkerHeight", 0.7)

    mapCorners = kwargs.get("mapCorners", [-90, -180, 90, 180])  # Lat1, Lon1, Lat2, Lon2 of a plotting region
    mapGrid = kwargs.get("mapGrid", "off")  # On to plot lat/lon grid lines
    mapLabelHeight = kwargs.get("mapLabelHeight", 0.4)
    mapRivers = kwargs.get("mapRivers", "off")  # On to plot major rivers

    outputWidth = kwargs.get("outputWidth", 1800)
    textFontSize = kwargs.get("textFontSize", 1.0)
    unitString = kwargs.get("unitString", "")
    windDensity = kwargs.get("windDensity", 2.5)
    windFieldType = kwargs.get("windFieldType", "arrows")  # Choices are "flags", "arrows", "streamlines"

    plot_shaded = fieldset.select(shortName=shortName,
                                  level=level) * scaleFactor + scaleBias

    plot_u = None
    plot_v = None
    plot_uv = None
    if plotWind:
        plot_u = fieldset.select(shortName='u', level=level)
        plot_v = fieldset.select(shortName='v', level=level)
        plot_uv = mv.merge(plot_u, plot_v)

    contours = mv.mcont(legend="on",
                        contour_automatics_settings="style_name",
                        contour_style_name=styleName)

    coastlines = mv.mcoast(
        map_administrative_boundaries=mapAdministrativeBoundaries,
        map_administrative_boundaries_countries_list=mapAdministrativeBoundariesCountriesList,
        map_administrative_boundaries_colour=mapAdministrativeBoundariesColour,
        map_administrative_boundaries_thickness=mapAdministrativeBoundariesThickness,
        map_administrative_boundaries_style=mapAdministrativeBoundariesStyle,
        map_boundaries=mapBoundaries,
        map_boundaries_colour=mapBoundariesColour,
        map_boundaries_thickness=mapBoundariesThickness,
        map_cities=mapCities,
        map_cities_font_size=mapCitiesFontSize,
        map_cities_marker_height=mapCitiesMarkerHeight,
        map_coastline_colour="charcoal",
        map_coastline_land_shade=mapCoastLandShade,
        map_coastline_land_shade_colour="beige",
        map_coastline_sea_shade=mapCoastSeaShade,
        map_coastline_sea_shade_colour="RGB(0.8178,0.9234,0.9234)",
        map_coastline_thickness=mapCoastLineThickness,
        map_disputed_boundaries="on",
        map_disputed_boundaries_thickness=mapBoundariesThickness,
        map_grid=mapGrid,
        map_grid_line_style="dash",
        map_grid_colour="navy",
        map_grid_latitude_increment=coastLatSpacing,
        map_grid_longitude_increment=coastLonSpacing,
        map_label_colour="black",
        map_label_font_style="bold",
        map_label_height=mapLabelHeight,
        map_rivers=mapRivers,
    )

    legend = mv.mlegend(
        legend_text_font_size=0.5
    )

    if mapAreaName:
        view = mv.geoview(
            area_mode="name",
            area_name=mapAreaName,
            coast=coastlines
        )
    else:
        view = mv.geoview(
            map_area_definition="corners",
            area=mapCorners,
            coast=coastlines
        )
    # define wind plotting
    wdef = mv.mwind(
        wind_thinning_mode="density",
        wind_density=windDensity,
        wind_field_type=windFieldType,
    )

    lon_arr = []
    lat_arr = []
    for i in range(0, len(line), 2):
        lat_arr.append(line[i])
        lon_arr.append(line[i + 1])

    vis_line = mv.input_visualiser(
        input_plot_type="geo_points",
        input_longitude_values=lon_arr,
        input_latitude_values=lat_arr,
    )

    graph_line = mv.mgraph(graph_line_colour="black", graph_line_thickness=4)

    # set-up the title
    field_level = "<grib_info key='level'/>"
    field_name = "<grib_info key='name'/>"
    field_shortName = "<grib_info key='shortName'/>"
    field_valid = "<grib_info key='valid-date' format='%a %d %b %Y %H UTC'/>"
    filter_valid = "<grib_info key='valid-date' format='%a %d %b %Y %H UTC' where='shortName=ws'/>"
    field_units = "<grib_info key='units'/>"
    filter_units = "<grib_info key='units' where='shortName=ws'/>"
    filter_level = "<grib_info key='level' where='shortName=ws'/>"
    if unitString:
        title_text = "ERA5 {} ({}) for {} on level {}".format(
            field_name, unitString, field_valid, field_level)
        filter_text = "ERA5 Wind ({}) {} {}".format(
            unitString, filter_valid, filter_level)
    else:
        title_text = "ERA5 {} ({}) for {} on level {}".format(
            field_name, field_units, field_valid, field_level)
        filter_text = "ERA5 Wind ({}) {} on level {}".format(
            filter_units, filter_valid, filter_level)

    title = mv.mtext(
        text_font_size=textFontSize,
        text_lines=[
            title_text,
        ],
        text_colour="CHARCOAL",
    )

    wind_title = mv.mtext(
        text_font_size=textFontSize,
        text_lines=[
            filter_text,
        ]
    )

    mv.setoutput("jupyter", output_width=outputWidth)

    if plotWind:
        if plotLine:
            mv.plot(view, plot_shaded, contours,
                    plot_uv, wdef, vis_line,
                    graph_line, legend, wind_title)
        else:
            mv.plot(view, plot_shaded, contours,
                    plot_uv, wdef, legend, wind_title)
    else:
        if plotLine:
            mv.plot(view, plot_shaded, contours,
                    vis_line, graph_line, legend, title)
        else:
            mv.plot(view, plot_shaded, contours,
                    legend, title)

    del plot_shaded
    del plot_u
    del plot_v
    del plot_uv
