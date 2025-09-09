package prac3;

import io.reactivex.rxjava3.core.Observable;

import java.util.Random;

public class Task2_1 {
    public static void main(String[] args) {
        third();
    }

    private static void first() {
        Observable.range(0, 1000)
                .map((value) -> new Random().nextInt(0, 1000))
                .map((value) -> value * value)
                .blockingSubscribe(System.out::println);
    }

    private static void second() {
        var flow1 = Observable.range(0, 1000).map((value) -> {
                    var random = new Random();
                    var index = random.nextInt(0, 26);
                    return Character.toString('A' + index);
                });
        var flow2 = Observable.range(0, 1000).map((value) -> new Random().nextInt(0, 10));

        Observable.zip(flow1, flow2, (f1, f2) -> f1 + f2)
                .blockingSubscribe(System.out::println);
    }

    private static void third() {
        Observable.range(0, 10).map((value) -> new Random().nextInt(0, 1000))
                .skip(3)
                .blockingSubscribe(System.out::println);
    }
}
