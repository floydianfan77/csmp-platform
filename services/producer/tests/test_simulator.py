"""Unit tests for the traffic simulator."""

from traffic_producer.simulator import TrafficSimulator, load_intersections


def test_load_intersections_from_seed(seed_csv_path):
    rows = load_intersections(seed_csv_path)
    assert len(rows) >= 3
    assert rows[0].intersection_id.startswith("osm-")


def test_generate_batch_covers_every_intersection(seed_csv_path):
    intersections = load_intersections(seed_csv_path)
    simulator = TrafficSimulator(intersections, seed=7)
    batch = simulator.generate_batch()
    assert len(batch) == len(intersections)
    assert {event.intersection_id for event in batch} == set(simulator.intersection_ids)
    for event in batch:
        assert event.environment.source.value == "simulator"
