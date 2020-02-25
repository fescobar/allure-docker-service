package com.allure.docker;

import com.allure.docker.listeners.MyListener;
import io.qameta.allure.Issue;
import io.qameta.allure.Link;
import io.qameta.allure.TmsLink;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Listeners;
import org.testng.annotations.Test;

import java.util.ArrayList;
import java.util.List;

@Listeners(MyListener.class)
public class ThirdTest {
    private static final Logger LOGGER = LoggerFactory.getLogger(ThirdTest.class.getName());

    @TmsLink("test-ticket-1")
    @Test(dataProvider = "products")
    public void test5(Product product) {
        LOGGER.info("test5", product);
    }

    @Issue("issue-ticket-7")
    @Test
    public void test6() {
        LOGGER.info("test6");
    }

    @Link(name = "some-link", type = "whatever")
    @Test
    public void test7() {
        LOGGER.info("test7");
    }

    @DataProvider(name = "products")
    public Object[] getProducts() {
        List<Product> productList = new ArrayList<Product>();
        productList.add(new Product("Product1",50.0));
        productList.add(new Product("Product2",982.30));
        return productList.toArray();
    }

    private class Product {
        private String name;
        private Double price;

        public Product() {
        }

        public Product(String name, Double price) {
            this.name = name;
            this.price = price;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public Double getPrice() {
            return price;
        }

        public void setPrice(Double price) {
            this.price = price;
        }

        @Override
        public String toString() {
            return "Product{" +
                    "name='" + name + '\'' +
                    ", price=" + price +
                    '}';
        }
    }
}
