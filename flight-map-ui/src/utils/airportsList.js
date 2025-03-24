export const loadAirportOptions = async () => {
    try {
        const response = await fetch('/airline_routes.json');
        const data = await response.json();

        const options = Object.keys(data).map((iata) => ({
            value: iata,
            label: `${iata} - ${data[iata].name}`
        }));

        return options;
    } catch (err) {
        console.error("Failed to load airport data:", err);
        return [];
    }
};