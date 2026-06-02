import secrets
import uuid

import pyotp
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Year(models.Model):
    """
    Represents a year model for storing unique year values.

    This class is designed for use in applications where unique year values need
    to be persisted in a database. The class ensures that each year is both unique
    and positive, which can be useful in scenarios such as event management,
    academic years, or yearly reports.

    Attributes:
        year (PositiveIntegerField): A unique and positive integer representing
            a specific year.
    """
    year = models.PositiveIntegerField(unique=True)


class Continent(models.Model):
    """
    Represents a continent with a unique name.

    This class is used to store and manage information related to continents.
    Each continent is identified by a unique name.

    Attributes:
        continent_name (models.CharField): The name of the continent. It must be
            unique and can have a maximum length of 200 characters.
    """
    continent_name = models.CharField(max_length=200, unique=True)


class Region(models.Model):
    """
    Represents a geographical or defined region.

    This class is used to define and manage regions in the system. Each region
    is uniquely identified by its name.

    Attributes:
        region_name (models.CharField): The unique name of the region with a
            maximum length of 200 characters.
    """
    region_name = models.CharField(max_length=200, unique=True)


class Country(models.Model):
    """Represents a country with associated metadata such as continent, region, and cost classification.

    This model is used to store and manage information about countries,
    including their association with a specific continent and region,
    a unique country code, and their classification as high-cost or low-cost.
    It is referenced by other tables within the database for relational operations.

    Attributes:
        country_name (str): The unique name of the country.
        continent (Continent): The continent to which the country belongs.
        region (Region): The region to which the country belongs.
        country_code (str): A default country code, set to "de".
    """

    class HccLcc(models.TextChoices):
        """A choice/enum class to mark the country as either high-cost or low-cost.
        """

    country_name = models.CharField(max_length=200, unique=True)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    country_code = models.CharField(max_length=200, default="de")

    class Meta:
        # db_table_comment = "Countries referenced by other tables"
        verbose_name = "Country"
        verbose_name_plural = "Countries"


class Industry(models.Model):
    """Represents an industry with a unique name.

    This model is used to store and identify different industries by their
    unique names. It enforces uniqueness for the industry name to prevent
    duplicate entries in the database.

    Attributes:
        industry_name (CharField): The unique name of the industry with a
        maximum length of 200 characters.
    """
    industry_name = models.CharField(max_length=200, unique=True)


class RegionValues(models.Model):
    """
    Represents a geographical or defined region.

    This class is used to define and manage regions in the system. Each region
    is uniquely identified by its name.

    Attributes:
        region_name (models.CharField): The unique name of the region with a
            maximum length of 200 characters.
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    profit_margin = models.FloatField(null=True, blank=True)
    profit_margin_real_value_status = models.BooleanField(default=False)


class Customer(models.Model):
    """
    Represents a customer company and its associated metadata.

    This class models a customer company, capturing its name, associated buyers,
    headquarter details, and industries it is involved in, along with corresponding
    scores. It allows creating, modifying, and accessing customer-related data that
    is integral to the system's operations.


    """
    customer_name = models.CharField(max_length=200, unique=True, verbose_name="Customer name",
                                     db_comment="Name of the customer company")
    headquarter_address = models.ForeignKey("GeoCoordinates", on_delete=models.SET_NULL,
                                            verbose_name="Customer's address",
                                            db_comment="Address of the customer company, without country", null=True,
                                            blank=True)
    headquarter_country = models.ForeignKey("Country", on_delete=models.SET_NULL, verbose_name="Customer's country",
                                            db_comment="Country the customer company resides in", null=True, blank=True)

    def __str__(self):
        return f"{self.customer_name}"


class ProductCluster(models.Model):
    """
    Represents a product cluster associated with a specific industry.

    This class models a grouping of products, identified by a unique name,
    and associates them with an industry. It is part of a database schema,
    utilizing Django's ORM features to define the relationships and constraints.

    Attributes:
        product_cluster_name (models.CharField): The unique name of the product cluster,
            with a maximum length of 200 characters.
        industry (models.ForeignKey): A foreign key relationship linking this product cluster
            to an Industry instance. Deleting the associated industry cascades the deletion
            to the related product cluster.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="product_cluster_customer_id")
    product_cluster_name = models.CharField(max_length=200, unique=True)
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)

    def __str__(self):
        return self.product_cluster_name


class ProductGroup(models.Model):
    """
    Represents a group of products categorized based on specific criteria.

    The ProductGroup class organizes products into groups for better management
    and categorization. Each product group is uniquely identified by its name and
    is associated with an industry and a product cluster. This model helps in
    structuring product-related data in a way that aligns with business needs.

    Attributes:
        product_group_name (str): The unique name of the product group.
        industry (ForeignKey): The associated industry to which the product group belongs.
        product_cluster (ForeignKey): The product cluster associated with this product group.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="product_group_customer_id")
    product_group_name = models.CharField(max_length=200, unique=True)
    product_cluster = models.ForeignKey(ProductCluster, on_delete=models.CASCADE)


class Product(models.Model):
    """
    Represents a product in the system.

    This class defines a product with its associated name, industry, cluster,
    and group. It is used for managing and categorizing products in the system.
    The attributes provide essential details required for product tracking and
    classification.

    Attributes:
        product_name (models.CharField): The unique name of the product.
        industry (models.ForeignKey): A reference to the industry the product
            belongs to. Deletes the product on removal of the industry.
        product_cluster (models.ForeignKey): A reference to the cluster
            associated with the product. Deletes the product on removal of
            the product cluster.
        product_group (models.ForeignKey): A reference to the group the product
            is categorized under. Deletes the product on removal of the product
            group.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="product_customer_id")
    product_name = models.CharField(max_length=200, unique=True)
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE)


class TrademarkGroup(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="trademark_group_customer_id")
    trademark_group_name = models.CharField(max_length=200, unique=True)


class ProductDescription(models.Model):
    """
    Represents a product in the system.

    This class defines a product with its associated name, industry, cluster,
    and group. It is used for managing and categorizing products in the system.
    The attributes provide essential details required for product tracking and
    classification.

    Attributes:
        product_name (models.CharField): The unique name of the product.
        industry (models.ForeignKey): A reference to the industry the product
            belongs to. Deletes the product on removal of the industry.
        product_cluster (models.ForeignKey): A reference to the cluster
            associated with the product. Deletes the product on removal of
            the product cluster.
        product_group (models.ForeignKey): A reference to the group the product
            is categorized under. Deletes the product on removal of the product
            group.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True,
                                 related_name="product_description_customer_id")

    product_description_name = models.CharField(max_length=200, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    trademark_group = models.ForeignKey(TrademarkGroup, on_delete=models.CASCADE,
                                        related_name="product_description_trademark_group")


class Buyer(models.Model):
    """
    Represents a buyer and their associated industries and scores.

    This class is designed to store buyer information such as the buyer's name,
    associated industries, and scores related to these industries. Industries
    are linked through foreign key relationships to an Industry model, allowing
    for flexible and scalable associations. Scores are optional and are used to
    represent the buyer's evaluation or involvement within a particular industry.

    Attributes:
        buyer_name (str): The unique name of the buyer.
        industry_1 (Industry): First associated industry for the buyer.
        industry_2 (Industry): Second associated industry for the buyer.
        industry_3 (Industry): Third associated industry for the buyer.
        industry_4 (Industry): Fourth associated industry for the buyer.
        industry_5 (Industry): Fifth associated industry for the buyer.
        industry_1_score (float): Score for the first associated industry; optional.
        industry_2_score (float): Score for the second associated industry; optional.
        industry_3_score (float): Score for the third associated industry; optional.
        industry_4_score (float): Score for the fourth associated industry; optional.
        industry_5_score (float): Score for the fifth associated industry; optional.
    """
    buyer_name = models.CharField(max_length=200, unique=True)
    public_own = models.IntegerField(null=True, blank=True)
    public_holding = models.IntegerField(null=True, blank=True)
    holding_name = models.CharField(max_length=500, null=True, blank=True)
    ticket_own = models.CharField(max_length=50, null=True, blank=True)
    ticket_holding = models.CharField(max_length=50, null=True, blank=True)
    # Links this buyer to a Salesforce Account so the map can show its notes.
    salesforce_account_id = models.CharField(max_length=18, null=True, blank=True, db_index=True)


class GeoCoordinates(models.Model):
    """
    Represents geographical coordinates associated with a country and city.

    This class is used to define and store geographical data such as the country, city,
    latitude, longitude, and whether the location is a capital city. It utilizes a database
    model for structured storage and management of this information.

    Attributes:
        country (ForeignKey): Reference to the associated country. Utilizes a ForeignKey
            relation to the Country model. On deletion of the country, related
            GeoCoordinates entries will also be deleted (CASCADE behavior).
        city (str): Name of the city. Current length is set to a maximum of
            120 characters; see the TODO note for future modifications.
        lat (float or None): Latitude coordinate of the geographical location. Can be
            null if not specified.
        lng (float or None): Longitude coordinate of the geographical location. Can be
            null if not specified.
        capital (bool or None): Indicates whether the location represents a capital city.
            Defaults to False but can be null if unspecified.
    """
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    city = models.CharField(max_length=120)
    lat = models.FloatField()
    lng = models.FloatField()
    capital = models.BooleanField()
    state = models.CharField(max_length=120, null=True)


class BuyerPlants(models.Model):
    """
    Represents a Customer Plant entity in the database.

    The class serves as a representation of a customer plant in the business context.
    It associates customer plants with their respective customer, location (continent,
    country, city), postal information, and address. Additionally, this model allows
    linking a customer plant to multiple product clusters, providing flexibility for
    organizational and operational purposes.

    Attributes:
        customer_plant_name (CharField): Name of the customer plant, defined as a
            unique value, and limited to 200 characters.
        customer (ForeignKey): ForeignKey relation to the `Customer` model, specifying
            the customer associated with this plant.
        continent (ForeignKey): ForeignKey relation to the `Continent` model, representing
            the continent where the plant is located.
        country (ForeignKey): ForeignKey relation to the `Country` model, specifying the
            country in which the customer plant is situated.
        city (ForeignKey): ForeignKey relation to the `GeoCoordinates` model, identifying
            the city linked to the plant.
        postalcode (IntegerField): Postal code of the customer plant. This field may be
            null if not provided.
        address (CharField): Address of the customer plant, defined as a unique value, and
            limited to 200 characters.
        product_cluster_1 (ForeignKey): ForeignKey relation to the `ProductCluster` model,
            identifying the first product cluster associated with the customer plant. This
            field is optional.
        product_cluster_2 (ForeignKey): ForeignKey relation to the `ProductCluster` model,
            specifying the second product cluster tied to the customer plant. This field
            is optional.
        product_cluster_3 (ForeignKey): ForeignKey relation to the `ProductCluster` model,
            referring to the third product cluster linked to the plant. This field is optional.
        product_cluster_4 (ForeignKey): ForeignKey relation to the `ProductCluster` model,
            defining the fourth product cluster related to the customer plant. This field
            is optional.
        product_cluster_5 (ForeignKey): ForeignKey relation to the `ProductCluster` model,
            indicating the fifth product cluster associated with the customer plant. This
            field is optional.
    """
    buyer_plant_name = models.CharField(max_length=200, verbose_name="Buyer Plant name",
                                        db_comment="Name of the Buyer Plant")
    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    city = models.ForeignKey(GeoCoordinates, on_delete=models.CASCADE)
    postalcode = models.CharField(null=True, max_length=20)
    address = models.CharField(null=True, max_length=200, verbose_name="Address of the customer",
                               db_comment="Address of the customer")


class CustomerPlants(models.Model):
    customer_plant_name = models.CharField(max_length=200, verbose_name="Customer Plant name",
                                           db_comment="Name of the Customer Plant")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    city = models.ForeignKey(GeoCoordinates, on_delete=models.CASCADE)
    postalcode = models.CharField(null=True, max_length=20)
    address = models.CharField(null=True, max_length=200, verbose_name="Address of the customer plant",
                               db_comment="Address of the customer plant")


class CustomerPeriod(models.Model):
    """
    Represents a date period associated with a customer.

    This class is used to define a specific date range assigned to a customer. It includes
    details such as the customer owning the period, the start and end dates, and additional
    metadata that may be useful for grouping or identification purposes.

    Attributes:
        customer (Customer): The customer associated with this date period.
            The relationship is modeled as a foreign key with CASCADE deletion.
        begin (date): The start date of this period indicating when it begins.
        end (date): The end date of this period indicating when it finishes.
        name (str): A name given by the customer for the identification of this period.
        year (Year): The year associated with this period, related as a foreign key
            with CASCADE deletion.
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Customer",
                                 db_comment="Customer using this date period")
    begin = models.DateField(verbose_name="Begin Date", db_comment="Date the period begins on")
    end = models.DateField(verbose_name="End Date", db_comment="Date the period ends on")
    name = models.CharField(max_length=200, verbose_name="date period name",
                            db_comment="name given by the Customer to this date period for identification")
    year = models.ForeignKey(Year, on_delete=models.CASCADE)


class ItemsToCustomerPeriods(models.Model):
    """
    Represents the relationship between items and customer periods with relevant attributes.

    This model is used to track and store the association between specific items, customers,
    and periods along with related details such as spend, quantity, and geographical
    information about buyers and customers. It includes foreign key relationships to
    other related models for deeper data linkage and analysis.

    Attributes:
        name (str): Name or title of the item, limited to 200 characters. Can be null.
        product_cluster (ProductCluster): Foreign key to ProductCluster, representing the related product cluster. Can be null.
        product_group (ProductGroup): Foreign key to ProductGroup, representing the related product group. Can be null.
        product (Product): Foreign key to Product, representing the specific product. Can be null.
        buyer (Buyer): Foreign key to Buyer, representing the buyer associated with this record.
        customerperiod (CustomerPeriod): Foreign key to CustomerPeriod, representing the period associated with the customer.
        spend (int): The amount spent by the buyer, stored as a big integer.
        quantity (int): The quantity of the product purchased, stored as a big integer.
        fault_ppm (int): Fault parts per million value. Can be null or blank.
        variety (int): Represents the variety of the product. Can be null or blank. Includes database comment and verbose name as "Variety".
        address_buyer (GeoCoordinates): Foreign key to GeoCoordinates, representing the buyer's address.
        country_buyer (Country): Foreign key to Country, representing the buyer's country, with a related name for referencing.
        address_customer (GeoCoordinates): Foreign key to GeoCoordinates, representing the customer's address.
        country_customer (Country): Foreign key to Country, representing the customer's country, with a related name for referencing.
        granted_discount (float): The percentage or amount of discount granted for the transaction.
    """
    name = models.CharField(max_length=200, null=True)
    product_cluster = models.ForeignKey(ProductCluster, on_delete=models.CASCADE)
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_description = models.ForeignKey(ProductDescription, on_delete=models.CASCADE)

    buyer = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    buyer_plant = models.ForeignKey(BuyerPlants, on_delete=models.CASCADE)
    customerperiod = models.ForeignKey(CustomerPeriod, on_delete=models.CASCADE)
    spend = models.BigIntegerField()
    quantity = models.FloatField()
    fault_ppm = models.IntegerField(null=True, blank=True)
    address_buyer = models.ForeignKey(GeoCoordinates, related_name='address_buyer', on_delete=models.CASCADE)
    country_buyer = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='country_buyer_id')
    address_customer = models.ForeignKey(GeoCoordinates, related_name='address_customer', on_delete=models.CASCADE)
    country_customer = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='country_customer_id')
    granted_discount = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['product_group_id', 'country_customer_id'], name="idx_prod_group_count_cust"),
            models.Index(fields=['buyer_id', 'country_buyer_id'], name="idx_buy_count_buy"),
            models.Index(
                fields=['product_id', 'product_group_id', 'buyer_id', 'country_buyer_id', 'country_customer_id'],
                name="idx_prod_grp_by_cot_by_cnt_cst"),
            models.Index(fields=['buyer_id', 'address_customer', 'address_buyer'], name="idx_buy_add_cust_add_buy"),
        ]


class SysLogEntry(models.Model):
    """
    Represents a system log entry.

    This class is used to store log entries related to system events or activities.
    Each entry is associated with a user, a message describing the log, and the
    timestamp when the log was created. It provides a structure to track system
    events and identify the user responsible (if applicable).

    Attributes:
        user (ForeignKey): A reference to the User who triggered the event. Can be
            null if no user is associated with the log entry.
        message (TextField): A detailed description of the system event or activity.
        created (DateTimeField): The timestamp indicating when the log entry was
            created.
    """
    user = models.ForeignKey("User", null=True, on_delete=models.SET_NULL)
    message = models.TextField()
    created = models.DateTimeField()


class User(AbstractUser):
    """
    Represents a user in the application, extending functionality from AbstractUser.

    This class encapsulates additional attributes and methods for managing and
    persisting user-related information such as customer data, email details,
    and security-related operations like generating reset tokens and OTP secrets.

    Attributes:
        customer (Customer): A reference to the Customer model, representing
            the customer associated with the user. The relationship allows null
            values and can be blank.
        email (str): The unique email address of the user.
    """
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(unique=True)
    allowed_product_clusters = models.ManyToManyField(
        'ProductCluster',
        blank=True,
        related_name='allowed_users',
    )

    def generate_rest_token(self):
        token = secrets.token_urlsafe(64)
        reset_token = ResetPasswordToken.objects.create(user=self, token=token)
        return token, reset_token.uuid

    def generate_otp_secret(self):
        secret = pyotp.random_base32()
        otp_secret = OtpSecrets.objects.create(user=self, secret=secret, active=False)
        otp_secret.save()
        return otp_secret

    def __str__(self) -> str:
        """Returns a string representation of the User object.

        Returns
        -------
        str
            A string representation of the User object, consisting of its username.
        """

        return f"{self.username}"


def is_manager_or_above(user: User) -> bool:
    """
    Determines if a user belongs to the "Managers" group or higher.

    This function checks whether the given user is a member of the group
    named "Managers" by filtering the user's group memberships. It returns
    a boolean value indicating the user's membership status.

    Args:
        user (User): An instance representing the user whose group
            memberships are being evaluated.

    Returns:
        bool: True if the user is a member of the "Managers" group, otherwise False.
    """
    return user.groups.filter(name="Managers").exists()


def is_employee_or_above(user: User) -> bool:
    """
    Determines if the given user is an employee or has a higher-level role.

    This function checks if the user belongs to the "Employees" group or if they hold
    a managerial position or a higher-level role. It ensures that the user has at least
    employee-level permissions or above within the system.

    Args:
        user (User): The user whose role is being checked.

    Returns:
        bool: True if the user is an employee or has a managerial role or above,
        otherwise False.
    """
    return user.groups.filter(name="Employees").exists() or is_manager_or_above(user)


def user_has_cluster_access(user: User, cluster_ids: list) -> bool:
    """Returns True if the user is allowed to access all given ProductCluster IDs."""
    if is_manager_or_above(user):
        return True
    allowed = set(user.allowed_product_clusters.values_list('id', flat=True))
    if not allowed:
        return False
    return set(cluster_ids).issubset(allowed)


def user_has_product_access(user: User, product_ids: list) -> bool:
    """Returns True if the user is allowed to access all given Product IDs.

    Managers always have full access. Employees are checked against their
    allowed clusters. If no clusters are assigned, access is denied.
    """
    if is_manager_or_above(user):
        return True
    allowed = set(user.allowed_product_clusters.values_list('id', flat=True))
    if not allowed:
        return False
    cluster_ids = set(
        Product.objects
        .filter(id__in=product_ids)
        .values_list('product_group__product_cluster_id', flat=True)
    )
    return cluster_ids.issubset(allowed)


class OtpSecrets(models.Model):
    """
    Represents a model to store OTP secrets for users.

    This class is used for managing one-time password (OTP) related configurations
    and secrets for individual users. It links a user to their unique OTP secret
    and maintains relevant metadata such as creation time and activation status.

    Attributes:
        user (OneToOneField): A one-to-one relationship with the `User` model. Ensures each user
            has a unique OTP secret.
        secret (str): The OTP secret associated with the user, stored as a string of a
            maximum length of 32 characters.
        created (DateTime): Automatically captures the timestamp when the OTP secret instance
            is created.
        active (bool): Indicates if the OTP secret is currently active.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    secret = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.user.username}"


class ResetPasswordToken(models.Model):
    """
    Represents a token used for resetting a user's password.

    The ResetPasswordToken class is designed to securely store and manage password
    reset tokens associated with specific users. It ensures that tokens are unique
    and immutable once created. This class integrates with the Django ORM as a
    model and utilizes Django's password hashing utilities for securing tokens.

    Attributes:
        uuid (UUID): A unique identifier for the token, auto-generated upon creation.
        user (User): A reference to the user this reset token is associated with.
        token (str): A secure, hashed representation of the reset token string.
        created (datetime): The timestamp when the reset token was created.
    """
    uuid = models.UUIDField(editable=False, auto_created=True, unique=True, db_index=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, **kwargs):
        if self.pk is not None:
            raise ValueError("ResetPasswordToken is immutable")
        token = make_password(str(self.token))
        self.token = token
        return super().save(**kwargs)

    def __str__(self):
        return "Reset token: " + self.user.username + " - " + str(self.created)
