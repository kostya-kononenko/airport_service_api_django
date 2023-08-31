from django.db import models
from rest_framework.exceptions import ValidationError


class Airport(models.Model):
    class ClosestBigCity(models.TextChoices):
        very_close = "very_close", "very_close"
        close = "close", "close"
        average_proximity = "average proximity", "average proximity"
        far = "far", "far"
        very_far = "very_far", "very_far"

    name = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    closest_big_city = models.CharField(max_length=20,
                                        choices=ClosestBigCity.choices,
                                        default=ClosestBigCity.close)
    image = models.ImageField(null=True,
                              blank=True,
                              upload_to="images/airport/")

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="rout_source")
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name="rout_destination")
    distance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.source} - {self.destination}"


class Crew(models.Model):
    class CrewPosition(models.TextChoices):
        captain = "captain", "captain"
        first_mate = "first mate", "first mate"
        flight_engineer = "flight engineer", "flight engineer"
        onboard_systems_operator = "onboard systems operator", "onboard systems operator"
        navigator = "navigator", "navigator"
        steward = "steward", "steward"

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    crew_position = models.CharField(max_length=25,
                                     choices=CrewPosition.choices,
                                     default=CrewPosition.steward)
    image = models.ImageField(null=True,
                              blank=True,
                              upload_to="images/crew/")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class AirplaneType(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(null=True,
                              blank=True,
                              upload_to="images/airplane/")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Airplane Type"


class Airplane(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE, related_name="airplane")

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return self.name


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="flight")
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, related_name="flight")
    crew = models.ManyToManyField(Crew, related_name="flight")
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["-departure_time"]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("user.User", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.created_at)

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, related_name="tickets")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tickets")
    row = models.IntegerField()
    seat = models.IntegerField()

    def clean(self):
        for ticket_attr_value, ticket_attr_name, airplane_attr_name in [
            (self.row, "row", "rows"),
            (self.seat, "seat", "seats_in_row"),
        ]:
            count_attrs = getattr(
                self.flight.airplane, airplane_attr_name
            )
            if not (1 <= ticket_attr_value <= count_attrs):
                raise ValidationError(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {airplane_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        super(Ticket, self).save(
            force_insert, force_update, using, update_fields
        )

    def __str__(self):
        return (
            f"{str(self.flight)} (row: {self.row}, seat: {self.seat})"
        )

    class Meta:
        unique_together = ("flight", "row", "seat")
