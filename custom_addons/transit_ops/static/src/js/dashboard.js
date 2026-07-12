/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TransitOpsDashboard extends Component {
    static template = "transit_ops.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            kpis: {},
            loading: true,
        });
        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        this.state.loading = true;
        try {
            const Vehicle = "transit.vehicle";
            const Driver = "transit.driver";
            const Trip = "transit.trip";
            const Maintenance = "transit.maintenance";

            // Fetch counts via ORM
            const [vehicles, drivers, trips, maintenanceRecords] = await Promise.all([
                this.orm.searchRead(Vehicle, [], ["status", "vehicle_type", "region"]),
                this.orm.searchRead(Driver, [], ["status", "license_status", "safety_score"]),
                this.orm.searchRead(Trip, [], ["state", "cargo_weight", "fuel_consumed", "fuel_cost"]),
                this.orm.searchRead(Maintenance, [], ["state"]),
            ]);

            const activeVehicles = vehicles.filter(v => v.status !== "retired");
            const availableVehicles = vehicles.filter(v => v.status === "available");
            const onTripVehicles = vehicles.filter(v => v.status === "on_trip");
            const inShopVehicles = vehicles.filter(v => v.status === "in_shop");

            const activeTrips = trips.filter(t => t.state === "dispatched");
            const pendingTrips = trips.filter(t => t.state === "draft");
            const completedTrips = trips.filter(t => t.state === "completed");
            const driversOnDuty = drivers.filter(d => d.status === "on_trip");
            const expiringLicenses = drivers.filter(d => d.license_status === "expiring" || d.license_status === "expired");

            const utilisation = activeVehicles.length > 0
                ? Math.round((onTripVehicles.length / activeVehicles.length) * 100)
                : 0;

            const totalFuelCost = completedTrips.reduce((sum, t) => sum + (t.fuel_cost || 0), 0);
            const openMaintenance = maintenanceRecords.filter(m => m.state === "open" || m.state === "in_progress");

            this.state.kpis = {
                activeVehicles: activeVehicles.length,
                availableVehicles: availableVehicles.length,
                onTripVehicles: onTripVehicles.length,
                inMaintenance: inShopVehicles.length,
                activeTrips: activeTrips.length,
                pendingTrips: pendingTrips.length,
                completedTrips: completedTrips.length,
                driversOnDuty: driversOnDuty.length,
                totalDrivers: drivers.length,
                utilisation: utilisation,
                expiringLicenses: expiringLicenses.length,
                totalFuelCost: Math.round(totalFuelCost),
                openMaintenance: openMaintenance.length,
            };
        } catch (e) {
            console.error("Dashboard load error:", e);
        }
        this.state.loading = false;
    }

    openAction(resModel, viewMode, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name,
            res_model: resModel,
            view_mode: viewMode,
            views: viewMode.split(",").map(vm => [false, vm.trim()]),
            target: "current",
        });
    }

    onNewTrip() { this.openAction("transit.trip", "form", "New Trip"); }
    onViewTrips() { this.openAction("transit.trip", "list,kanban,form", "Trip Dispatcher"); }
    onViewVehicles() { this.openAction("transit.vehicle", "list,form", "Fleet"); }
    onViewDrivers() { this.openAction("transit.driver", "list,form", "Drivers"); }
    onViewMaintenance() { this.openAction("transit.maintenance", "list,form", "Maintenance"); }
    onViewFuelLogs() { this.openAction("transit.fuel.log", "list,form", "Fuel Logs"); }
    async onRefresh() { await this.loadDashboard(); }
    onExportPDF() { window.print(); }
}

registry.category("actions").add("transit_ops.dashboard", TransitOpsDashboard);
